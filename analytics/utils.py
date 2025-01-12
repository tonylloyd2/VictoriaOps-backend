from django.utils import timezone
from datetime import timedelta
from django.db.models import Avg, Count, Sum
import pandas as pd
import numpy as np

def calculate_trend(values, periods=7):
    """Calculate trend direction and percentage change"""
    if not values or len(values) < 2:
        return {'direction': 'stable', 'change_percentage': 0}
    
    values = np.array(values)
    change = (values[-1] - values[0]) / values[0] * 100 if values[0] != 0 else 0
    
    if change > 0:
        direction = 'up'
    elif change < 0:
        direction = 'down'
    else:
        direction = 'stable'
    
    return {
        'direction': direction,
        'change_percentage': abs(change)
    }

def get_time_series_data(queryset, date_field, start_date, end_date, interval='daily'):
    """Generate time series data for analytics"""
    data = queryset.filter(
        **{f"{date_field}__gte": start_date, f"{date_field}__lte": end_date}
    )
    
    if interval == 'hourly':
        return data.annotate(
            period=timezone.datetime.strftime(f"{date_field}", '%Y-%m-%d %H:00')
        ).values('period').annotate(count=Count('id')).order_by('period')
    
    elif interval == 'daily':
        return data.annotate(
            period=timezone.datetime.strftime(f"{date_field}", '%Y-%m-%d')
        ).values('period').annotate(count=Count('id')).order_by('period')
    
    elif interval == 'weekly':
        return data.annotate(
            period=timezone.datetime.strftime(f"{date_field}", '%Y-W%W')
        ).values('period').annotate(count=Count('id')).order_by('period')
    
    elif interval == 'monthly':
        return data.annotate(
            period=timezone.datetime.strftime(f"{date_field}", '%Y-%m')
        ).values('period').annotate(count=Count('id')).order_by('period')
    
    return None

def calculate_kpi_status(current, target):
    """Calculate KPI status and completion percentage"""
    if target == 0:
        return {
            'status': 'undefined',
            'completion': 0,
            'remaining': 0
        }
    
    completion = (current / target) * 100
    
    if completion >= 100:
        status = 'achieved'
    elif completion >= 75:
        status = 'on_track'
    elif completion >= 50:
        status = 'needs_attention'
    else:
        status = 'at_risk'
    
    return {
        'status': status,
        'completion': completion,
        'remaining': target - current
    }

def generate_summary_statistics(data_frame):
    """Generate summary statistics for numerical data"""
    if data_frame.empty:
        return {}
    
    numeric_cols = data_frame.select_dtypes(include=[np.number]).columns
    
    stats = {}
    for col in numeric_cols:
        stats[col] = {
            'mean': data_frame[col].mean(),
            'median': data_frame[col].median(),
            'std': data_frame[col].std(),
            'min': data_frame[col].min(),
            'max': data_frame[col].max(),
            'q1': data_frame[col].quantile(0.25),
            'q3': data_frame[col].quantile(0.75)
        }
    
    return stats
