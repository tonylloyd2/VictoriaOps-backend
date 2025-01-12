from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from datetime import timedelta
from django.db.models import Avg, Count, Sum, F, Q
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
import base64

from .models import (
    AnalyticsEvent, Report, KPI, KPIHistory, 
    Alert, DataAggregation
)
from .serializers import (
    AnalyticsEventSerializer, ReportSerializer, KPISerializer,
    KPIHistorySerializer, AlertSerializer, DataAggregationSerializer
)
from .tasks import generate_report, check_kpi_alerts

class AnalyticsEventViewSet(viewsets.ModelViewSet):
    queryset = AnalyticsEvent.objects.all()
    serializer_class = AnalyticsEventSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['event_type', 'event_name']

    @action(detail=False, methods=['get'])
    def event_summary(self, request):
        """Get summary of events by type for the last 30 days"""
        thirty_days_ago = timezone.now() - timedelta(days=30)
        summary = (
            self.queryset
            .filter(timestamp__gte=thirty_days_ago)
            .values('event_type')
            .annotate(
                count=Count('id'),
                avg_per_day=Count('id') / 30.0
            )
        )
        return Response(summary)

    @action(detail=False, methods=['get'])
    def cross_reference_analysis(self, request):
        """Analyze relationships between different event types"""
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        events = self.queryset.filter(
            timestamp__range=[start_date, end_date]
        )

        # Convert to DataFrame for analysis
        df = pd.DataFrame(events.values())
        
        # Perform correlation analysis
        correlations = {}
        for type1 in df['event_type'].unique():
            for type2 in df['event_type'].unique():
                if type1 < type2:  # Avoid duplicate combinations
                    type1_events = df[df['event_type'] == type1]['timestamp']
                    type2_events = df[df['event_type'] == type2]['timestamp']
                    
                    # Calculate temporal correlation
                    correlation = calculate_temporal_correlation(type1_events, type2_events)
                    correlations[f"{type1}-{type2}"] = correlation

        return Response(correlations)

class ReportViewSet(viewsets.ModelViewSet):
    queryset = Report.objects.all()
    serializer_class = ReportSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['report_type']

    @action(detail=False, methods=['post'])
    def generate(self, request):
        """Generate a new report based on parameters"""
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            report = serializer.save()
            generate_report.delay(report.id)
            return Response({
                'status': 'Report generation started',
                'report_id': report.id
            }, status=status.HTTP_202_ACCEPTED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """Download the generated report file"""
        report = self.get_object()
        format_type = request.query_params.get('format', 'excel')
        
        if format_type == 'excel' and report.excel_file:
            return Response({'file_url': request.build_absolute_uri(report.excel_file.url)})
        elif format_type == 'pdf' and report.pdf_file:
            return Response({'file_url': request.build_absolute_uri(report.pdf_file.url)})
        elif format_type == 'csv' and report.csv_file:
            return Response({'file_url': request.build_absolute_uri(report.csv_file.url)})
        
        return Response(
            {'error': f'Report file not generated yet for format {format_type}'},
            status=status.HTTP_404_NOT_FOUND
        )

class KPIViewSet(viewsets.ModelViewSet):
    queryset = KPI.objects.all()
    serializer_class = KPISerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['category']

    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """Get KPI dashboard data with trends and alerts"""
        kpis = self.queryset.all()
        categories = kpis.values_list('category', flat=True).distinct()
        
        dashboard_data = {}
        for category in categories:
            category_kpis = kpis.filter(category=category)
            kpi_data = self.get_serializer(category_kpis, many=True).data
            
            # Add visualization data
            for kpi in kpi_data:
                kpi['visualization'] = self.generate_kpi_visualization(kpi['id'])
            
            dashboard_data[category] = kpi_data
        
        return Response(dashboard_data)

    @action(detail=True, methods=['post'])
    def update_value(self, request, pk=None):
        """Update KPI current value and check alerts"""
        kpi = self.get_object()
        new_value = request.data.get('value')
        
        if new_value is None:
            return Response(
                {'error': 'Value is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update KPI value
        kpi.current_value = new_value
        kpi.save()
        
        # Record history
        KPIHistory.objects.create(kpi=kpi, value=new_value)
        
        # Update trend data
        self.update_trend_analysis(kpi)
        
        # Check alerts
        check_kpi_alerts.delay(kpi.id)
        
        return Response(self.get_serializer(kpi).data)

    @action(detail=True, methods=['get'])
    def forecast(self, request, pk=None):
        """Generate forecast for KPI values"""
        kpi = self.get_object()
        days = int(request.query_params.get('days', 30))
        
        # Get historical data
        history = kpi.history.order_by('timestamp')
        if history.count() < 5:
            return Response({
                'error': 'Insufficient historical data for forecasting'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Prepare data for forecasting
        df = pd.DataFrame(history.values())
        X = (df['timestamp'] - df['timestamp'].min()).dt.total_seconds().values.reshape(-1, 1)
        y = df['value'].values
        
        # Train model
        model = LinearRegression()
        model.fit(X, y)
        
        # Generate forecast
        last_timestamp = df['timestamp'].max()
        future_seconds = np.array(range(1, days + 1)) * 86400
        future_values = model.predict(future_seconds.reshape(-1, 1))
        
        forecast_data = {
            'dates': [(last_timestamp + timedelta(days=i)).isoformat() for i in range(1, days + 1)],
            'values': future_values.tolist(),
            'confidence_interval': calculate_confidence_interval(model, X, y, future_seconds)
        }
        
        # Save forecast data
        kpi.forecast_data = forecast_data
        kpi.save()
        
        return Response(forecast_data)

    def generate_kpi_visualization(self, kpi_id):
        """Generate visualization for KPI trends"""
        kpi = KPI.objects.get(id=kpi_id)
        history = kpi.history.order_by('timestamp')
        
        if not history.exists():
            return None
        
        # Create visualization using matplotlib
        plt.figure(figsize=(10, 6))
        
        # Plot historical values
        dates = [h.timestamp for h in history]
        values = [h.value for h in history]
        plt.plot(dates, values, label='Actual')
        
        # Plot target line
        plt.axhline(y=kpi.target_value, color='r', linestyle='--', label='Target')
        
        # Add forecasted values if available
        if kpi.forecast_data:
            forecast_dates = [timezone.datetime.fromisoformat(d) for d in kpi.forecast_data['dates']]
            forecast_values = kpi.forecast_data['values']
            plt.plot(forecast_dates, forecast_values, 'g--', label='Forecast')
        
        plt.title(f'{kpi.name} Trend')
        plt.xlabel('Date')
        plt.ylabel(kpi.unit)
        plt.legend()
        
        # Save plot to bytes
        buffer = BytesIO()
        plt.savefig(buffer, format='png')
        plt.close()
        
        # Convert to base64
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        return f'data:image/png;base64,{image_base64}'

    def update_trend_analysis(self, kpi):
        """Update trend analysis for a KPI"""
        history = kpi.history.order_by('timestamp')
        if history.count() < 2:
            return
        
        df = pd.DataFrame(history.values())
        
        # Calculate trend direction and strength
        values = df['value'].values
        x = np.arange(len(values)).reshape(-1, 1)
        
        model = LinearRegression()
        model.fit(x, values)
        
        trend_data = {
            'direction': 'up' if model.coef_[0] > 0 else 'down',
            'strength': abs(model.coef_[0]),
            'change_rate': calculate_change_rate(values),
            'r_squared': model.score(x, values)
        }
        
        kpi.trend_data = trend_data
        kpi.save()

class AlertViewSet(viewsets.ModelViewSet):
    queryset = Alert.objects.all()
    serializer_class = AlertSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['status', 'severity', 'kpi']

    @action(detail=True, methods=['post'])
    def acknowledge(self, request, pk=None):
        """Acknowledge an alert"""
        alert = self.get_object()
        alert.status = 'acknowledged'
        alert.save()
        return Response(self.get_serializer(alert).data)

    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """Resolve an alert"""
        alert = self.get_object()
        alert.status = 'resolved'
        alert.save()
        return Response(self.get_serializer(alert).data)

class DataAggregationViewSet(viewsets.ModelViewSet):
    queryset = DataAggregation.objects.all()
    serializer_class = DataAggregationSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['aggregation_type', 'time_period']

    @action(detail=False, methods=['post'])
    def calculate_aggregation(self, request):
        """Calculate new data aggregation"""
        name = request.data.get('name')
        aggregation_type = request.data.get('aggregation_type')
        time_period = request.data.get('time_period')
        parameters = request.data.get('parameters', {})
        
        # Perform aggregation calculation
        result = calculate_aggregation(aggregation_type, time_period, parameters)
        
        aggregation = DataAggregation.objects.create(
            name=name,
            aggregation_type=aggregation_type,
            time_period=time_period,
            parameters=parameters,
            data=result
        )
        
        return Response(self.get_serializer(aggregation).data)

def calculate_temporal_correlation(events1, events2):
    """Calculate temporal correlation between two event series"""
    # Implementation details here
    return 0.0

def calculate_confidence_interval(model, X, y, future_X):
    """Calculate confidence interval for forecasted values"""
    # Implementation details here
    return {'lower': [], 'upper': []}

def calculate_change_rate(values):
    """Calculate rate of change for a series of values"""
    if len(values) < 2:
        return 0
    return (values[-1] - values[0]) / len(values)

def calculate_aggregation(aggregation_type, time_period, parameters):
    """Calculate data aggregation based on type and parameters"""
    # Implementation details here
    return {}
