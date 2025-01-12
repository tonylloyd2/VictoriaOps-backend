from rest_framework import serializers
from .models import (
    AnalyticsEvent, Report, KPI, KPIHistory, 
    Alert, DataAggregation
)

class AnalyticsEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnalyticsEvent
        fields = '__all__'
        read_only_fields = ('timestamp',)

class ReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = '__all__'
        read_only_fields = ('created_at', 'excel_file', 'pdf_file', 'csv_file', 'charts')

class KPIHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = KPIHistory
        fields = '__all__'
        read_only_fields = ('timestamp',)

class AlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alert
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')

class KPISerializer(serializers.ModelSerializer):
    achievement_percentage = serializers.SerializerMethodField()
    history = KPIHistorySerializer(many=True, read_only=True)
    alerts = AlertSerializer(many=True, read_only=True)
    trend = serializers.SerializerMethodField()

    class Meta:
        model = KPI
        fields = '__all__'
        read_only_fields = ('last_updated', 'trend_data', 'forecast_data')

    def get_achievement_percentage(self, obj):
        """Calculate the percentage of target achieved"""
        if obj.target_value != 0:
            return (obj.current_value / obj.target_value) * 100
        return 0

    def get_trend(self, obj):
        """Get the trend direction and strength"""
        if not obj.trend_data:
            return None
        
        return {
            'direction': obj.trend_data.get('direction'),
            'strength': obj.trend_data.get('strength'),
            'change_rate': obj.trend_data.get('change_rate')
        }

class DataAggregationSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataAggregation
        fields = '__all__'
        read_only_fields = ('last_updated',)
