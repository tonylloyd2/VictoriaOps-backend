from celery import shared_task
from django.core.files.base import ContentFile
from django.core.mail import send_mail
from django.conf import settings
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import json
from datetime import datetime
from io import BytesIO
import csv
import base64

@shared_task
def generate_report(report_id):
    """Generate report asynchronously"""
    from .models import Report, AnalyticsEvent  # Import here to avoid circular imports
    
    try:
        report = Report.objects.get(id=report_id)
        
        # Get events based on report parameters
        events = AnalyticsEvent.objects.filter(
            timestamp__gte=report.date_range_start,
            timestamp__lte=report.date_range_end
        )
        
        if report.parameters.get('event_type'):
            events = events.filter(event_type=report.parameters['event_type'])
        
        # Convert to pandas DataFrame for analysis
        events_data = []
        for event in events:
            event_dict = {
                'event_type': event.event_type,
                'event_name': event.event_name,
                'timestamp': event.timestamp,
                **event.data  # Unpack additional data
            }
            events_data.append(event_dict)
        
        df = pd.DataFrame(events_data)
        
        # Generate analysis based on report type
        if report.report_type == 'daily':
            analysis = generate_daily_report(df)
        elif report.report_type == 'weekly':
            analysis = generate_weekly_report(df)
        elif report.report_type == 'monthly':
            analysis = generate_monthly_report(df)
        elif report.report_type == 'trend':
            analysis = generate_trend_report(df)
        elif report.report_type == 'forecast':
            analysis = generate_forecast_report(df)
        else:
            analysis = generate_custom_report(df, report.parameters)
        
        # Save analysis results
        report.data = analysis
        
        # Generate visualizations
        charts = generate_report_charts(df, report.report_type)
        report.charts = charts
        
        # Generate files in requested format
        if report.format_type in ['excel', 'all']:
            generate_excel_report(report, df, analysis)
        
        if report.format_type in ['pdf', 'all']:
            generate_pdf_report(report, df, analysis, charts)
        
        if report.format_type in ['csv', 'all']:
            generate_csv_report(report, df)
        
        report.save()
        return True
        
    except Exception as e:
        print(f"Error generating report {report_id}: {str(e)}")
        return False

@shared_task
def check_kpi_alerts():
    """Check all KPIs for alert conditions"""
    from .models import KPI, Alert
    
    for kpi in KPI.objects.all():
        alerts = Alert.objects.filter(kpi=kpi, enabled=True, status='active')
        
        for alert in alerts:
            if alert.threshold_type == 'above' and kpi.current_value > alert.threshold_value:
                trigger_alert(alert)
            elif alert.threshold_type == 'below' and kpi.current_value < alert.threshold_value:
                trigger_alert(alert)

def trigger_alert(alert):
    """Handle alert triggering and notifications"""
    if 'email' in alert.notification_channels:
        send_alert_email(alert)
    
    if 'slack' in alert.notification_channels:
        send_slack_notification(alert)

def send_alert_email(alert):
    """Send alert notification via email"""
    subject = f"KPI Alert: {alert.title}"
    message = f"""
    Alert Details:
    KPI: {alert.kpi.name}
    Severity: {alert.severity}
    Description: {alert.description}
    Current Value: {alert.kpi.current_value} {alert.kpi.unit}
    Threshold: {alert.threshold_value} {alert.kpi.unit}
    """
    
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [settings.ALERT_EMAIL],
        fail_silently=False,
    )

def send_slack_notification(alert):
    """Send alert notification to Slack"""
    # Implementation for Slack notifications
    pass

def generate_daily_report(df):
    """Generate daily analytics report"""
    if df.empty:
        return {'error': 'No data available'}
    
    return {
        'total_events': len(df),
        'events_by_type': df['event_type'].value_counts().to_dict(),
        'hourly_distribution': df.groupby(df['timestamp'].dt.hour).size().to_dict(),
        'peak_hour': df.groupby(df['timestamp'].dt.hour).size().idxmax(),
    }

def generate_weekly_report(df):
    """Generate weekly analytics report"""
    if df.empty:
        return {'error': 'No data available'}
    
    return {
        'total_events': len(df),
        'events_by_type': df['event_type'].value_counts().to_dict(),
        'daily_distribution': df.groupby(df['timestamp'].dt.day_name()).size().to_dict(),
        'busiest_day': df.groupby(df['timestamp'].dt.day_name()).size().idxmax(),
    }

def generate_monthly_report(df):
    """Generate monthly analytics report"""
    if df.empty:
        return {'error': 'No data available'}
    
    return {
        'total_events': len(df),
        'events_by_type': df['event_type'].value_counts().to_dict(),
        'weekly_trend': df.groupby(df['timestamp'].dt.isocalendar().week).size().to_dict(),
        'month_summary': {
            'total_events': len(df),
            'unique_event_types': df['event_type'].nunique(),
            'most_common_event': df['event_type'].mode().iloc[0],
        }
    }

def generate_trend_report(df):
    """Generate trend analysis report"""
    if df.empty:
        return {'error': 'No data available'}
    
    # Resample data to daily frequency
    daily_counts = df.groupby([
        pd.Grouper(key='timestamp', freq='D'),
        'event_type'
    ]).size().unstack(fill_value=0)
    
    # Calculate trends
    trends = {}
    for column in daily_counts.columns:
        slope, intercept = np.polyfit(range(len(daily_counts)), daily_counts[column], 1)
        trends[column] = {
            'slope': slope,
            'trend_direction': 'increasing' if slope > 0 else 'decreasing',
            'average': daily_counts[column].mean(),
            'std_dev': daily_counts[column].std(),
        }
    
    return {
        'trends_by_type': trends,
        'overall_trend': {
            'total_events': len(df),
            'daily_average': len(df) / len(daily_counts),
            'volatility': daily_counts.sum(axis=1).std(),
        }
    }

def generate_forecast_report(df):
    """Generate forecast report"""
    if df.empty:
        return {'error': 'No data available'}
    
    # Group by date and event type
    daily_counts = df.groupby([
        pd.Grouper(key='timestamp', freq='D'),
        'event_type'
    ]).size().unstack(fill_value=0)
    
    forecasts = {}
    for event_type in daily_counts.columns:
        series = daily_counts[event_type]
        model = fit_forecast_model(series)
        forecast = generate_forecast(model, steps=30)  # 30 days forecast
        forecasts[event_type] = forecast
    
    return {
        'forecasts': forecasts,
        'confidence_intervals': calculate_forecast_confidence(forecasts),
        'accuracy_metrics': calculate_forecast_accuracy(daily_counts),
    }

def generate_custom_report(df, parameters):
    """Generate custom analytics report based on parameters"""
    if df.empty:
        return {'error': 'No data available'}
    
    analysis = {
        'total_events': len(df),
        'time_range': {
            'start': df['timestamp'].min().isoformat(),
            'end': df['timestamp'].max().isoformat(),
            'duration_days': (df['timestamp'].max() - df['timestamp'].min()).days,
        }
    }
    
    # Add custom analysis based on parameters
    if parameters.get('include_hourly'):
        analysis['hourly'] = df.groupby(df['timestamp'].dt.hour).size().to_dict()
    
    if parameters.get('include_daily'):
        analysis['daily'] = df.groupby(df['timestamp'].dt.date).size().to_dict()
    
    if parameters.get('event_correlations'):
        analysis['correlations'] = calculate_event_correlations(df)
    
    return analysis

def generate_report_charts(df, report_type):
    """Generate visualizations for the report"""
    charts = {}
    
    # Time series plot
    plt.figure(figsize=(12, 6))
    df.groupby([pd.Grouper(key='timestamp', freq='D'), 'event_type']).size().unstack().plot()
    plt.title('Events Over Time by Type')
    plt.xlabel('Date')
    plt.ylabel('Number of Events')
    
    buffer = BytesIO()
    plt.savefig(buffer, format='png')
    plt.close()
    charts['time_series'] = base64.b64encode(buffer.getvalue()).decode()
    
    # Event type distribution
    plt.figure(figsize=(8, 8))
    df['event_type'].value_counts().plot(kind='pie')
    plt.title('Event Type Distribution')
    
    buffer = BytesIO()
    plt.savefig(buffer, format='png')
    plt.close()
    charts['distribution'] = base64.b64encode(buffer.getvalue()).decode()
    
    return charts

def generate_excel_report(report, df, analysis):
    """Generate Excel report file"""
    excel_file = BytesIO()
    
    with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
        # Write summary sheet
        pd.DataFrame([analysis]).to_excel(writer, sheet_name='Summary', index=False)
        
        # Write detailed data
        df.to_excel(writer, sheet_name='Detailed Data', index=False)
        
        # Write pivot tables if applicable
        if len(df) > 0:
            pivot = pd.pivot_table(
                df,
                index=pd.Grouper(key='timestamp', freq='D'),
                columns='event_type',
                aggfunc='size',
                fill_value=0
            )
            pivot.to_excel(writer, sheet_name='Daily Breakdown')
    
    filename = f"report_{report.report_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    report.excel_file.save(filename, ContentFile(excel_file.getvalue()))

def generate_pdf_report(report, df, analysis, charts):
    """Generate PDF report file"""
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    
    # Add title
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(50, 800, f"Analytics Report: {report.title}")
    
    # Add summary
    pdf.setFont("Helvetica", 12)
    y = 750
    for key, value in analysis.items():
        if isinstance(value, (str, int, float)):
            pdf.drawString(50, y, f"{key}: {value}")
            y -= 20
    
    # Add charts if available
    if charts:
        for name, chart_data in charts.items():
            # Add chart image
            img_data = base64.b64decode(chart_data)
            img_buffer = BytesIO(img_data)
            pdf.drawImage(img_buffer, 50, y - 300, width=500, height=300)
            y -= 320
    
    pdf.save()
    
    filename = f"report_{report.report_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    report.pdf_file.save(filename, ContentFile(buffer.getvalue()))

def generate_csv_report(report, df):
    """Generate CSV report file"""
    buffer = BytesIO()
    df.to_csv(buffer, index=False)
    
    filename = f"report_{report.report_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    report.csv_file.save(filename, ContentFile(buffer.getvalue()))

def fit_forecast_model(series):
    """Fit a forecasting model to the time series"""
    # Implementation for time series forecasting
    pass

def generate_forecast(model, steps):
    """Generate forecast values"""
    # Implementation for generating forecast
    pass

def calculate_forecast_confidence(forecasts):
    """Calculate confidence intervals for forecasts"""
    # Implementation for confidence intervals
    pass

def calculate_forecast_accuracy(data):
    """Calculate accuracy metrics for the forecast"""
    # Implementation for accuracy metrics
    pass

def calculate_event_correlations(df):
    """Calculate correlations between different event types"""
    # Implementation for correlation analysis
    pass
