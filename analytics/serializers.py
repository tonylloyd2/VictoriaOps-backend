from rest_framework import serializers
from .models import (
    AnalyticsEvent, Report, KPI, KPIHistory, 
    Alert, DataAggregation, Department, ProductionMetrics, InventoryMetrics
)
from drf_spectacular.utils import extend_schema_field
from drf_spectacular.types import OpenApiTypes

class AnalyticsEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnalyticsEvent
        fields = ['id', 'event_type', 'name', 'description', 'data', 
                 'user', 'timestamp']
        read_only_fields = ('timestamp',)

class ReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = ['id', 'title', 'report_type', 'description', 'parameters',
                 'data', 'created_by', 'created_at', 'updated_at']
        read_only_fields = ('created_at', 'excel_file', 'pdf_file', 'csv_file', 'charts')

class KPIHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = KPIHistory
        fields = '__all__'
        read_only_fields = ('timestamp',)

class AlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alert
        fields = ['id', 'title', 'description', 'severity', 'is_active',
                 'data', 'created_at', 'resolved_at']
        read_only_fields = ('created_at', 'updated_at')

class KPISerializer(serializers.ModelSerializer):
    achievement_percentage = serializers.SerializerMethodField()
    trend = serializers.SerializerMethodField()

    class Meta:
        model = KPI
        fields = ['id', 'name', 'description', 'department', 'target_value', 
                 'current_value', 'unit', 'start_date', 'end_date', 
                 'achievement_percentage', 'trend', 'created_at', 'updated_at']
        read_only_fields = ('last_updated', 'trend_data', 'forecast_data')

    @extend_schema_field(OpenApiTypes.FLOAT)
    def get_achievement_percentage(self, obj):
        if obj.target_value and obj.target_value != 0:
            return (obj.current_value / obj.target_value) * 100
        return 0

    @extend_schema_field(OpenApiTypes.STR)
    def get_trend(self, obj):
        if not obj.previous_value:
            return "stable"
        if obj.current_value > obj.previous_value:
            return "increasing"
        elif obj.current_value < obj.previous_value:
            return "decreasing"
        return "stable"

class DataAggregationSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataAggregation
        fields = ['id', 'name', 'description', 'aggregation_type', 'data',
                 'parameters', 'last_updated', 'created_at']
        read_only_fields = ('last_updated',)

class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ['id', 'name', 'description', 'manager', 'created_at', 'updated_at']

class DepartmentDetailSerializer(DepartmentSerializer):
    kpis = KPISerializer(many=True, read_only=True)

    class Meta(DepartmentSerializer.Meta):
        fields = DepartmentSerializer.Meta.fields + ['kpis']

class ProductionMetricsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductionMetrics
        fields = ['id', 'date', 'production_line', 'output_quantity', 
                 'defect_rate', 'efficiency', 'downtime', 'notes',
                 'created_at', 'updated_at']

class InventoryMetricsSerializer(serializers.ModelSerializer):
    class Meta:
        model = InventoryMetrics
        fields = ['id', 'date', 'warehouse', 'stock_value', 'turnover_rate',
                 'stockout_incidents', 'notes', 'created_at', 'updated_at']
