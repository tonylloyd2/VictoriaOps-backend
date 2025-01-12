from django.contrib import admin
from django.utils.html import format_html
from .models import (
    AnalyticsEvent, EventMetadata, KPI, KPIHistory,
    Alert, Report, DataAggregation
)

class EventMetadataInline(admin.TabularInline):
    model = EventMetadata
    extra = 1

@admin.register(AnalyticsEvent)
class AnalyticsEventAdmin(admin.ModelAdmin):
    list_display = ('event_type', 'event_name', 'timestamp', 'value', 'unit', 'source_machine', 'source_department')
    list_filter = ('event_type', 'source_department', 'timestamp')
    search_fields = ('event_name', 'source_machine', 'source_department', 'source_operator')
    date_hierarchy = 'timestamp'
    inlines = [EventMetadataInline]
    fieldsets = (
        ('Event Information', {
            'fields': ('event_type', 'event_name', 'timestamp', 'value', 'unit', 'description')
        }),
        ('Source Details', {
            'fields': ('source_machine', 'source_department', 'source_operator')
        }),
    )

class KPIHistoryInline(admin.TabularInline):
    model = KPIHistory
    extra = 0
    readonly_fields = ('timestamp',)
    ordering = ('-timestamp',)
    max_num = 10

class AlertInline(admin.TabularInline):
    model = Alert
    extra = 0
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)
    max_num = 5

@admin.register(KPI)
class KPIAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'current_value', 'target_value', 'unit', 'status_indicator')
    list_filter = ('category', 'update_frequency')
    search_fields = ('name', 'description')
    inlines = [KPIHistoryInline, AlertInline]
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'category', 'unit')
        }),
        ('Values', {
            'fields': ('current_value', 'target_value')
        }),
        ('Alert Settings', {
            'fields': ('warning_threshold', 'critical_threshold')
        }),
        ('Trend Settings', {
            'fields': ('trend_period_days', 'update_frequency')
        }),
    )

    def status_indicator(self, obj):
        if obj.current_value >= obj.critical_threshold:
            color = 'red'
            status = 'Critical'
        elif obj.current_value >= obj.warning_threshold:
            color = 'orange'
            status = 'Warning'
        else:
            color = 'green'
            status = 'Normal'
        return format_html(
            '<span style="color: {};">{}</span>',
            color,
            status
        )
    status_indicator.short_description = 'Status'

@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ('title', 'kpi', 'severity', 'status', 'created_at', 'acknowledged_by')
    list_filter = ('severity', 'status', 'created_at')
    search_fields = ('title', 'description', 'kpi__name')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'acknowledged_at', 'resolved_at')
    fieldsets = (
        ('Alert Information', {
            'fields': ('kpi', 'title', 'description', 'severity', 'status')
        }),
        ('Values', {
            'fields': ('threshold_value', 'current_value')
        }),
        ('Resolution', {
            'fields': ('acknowledged_by', 'resolution_note', 'created_at', 'acknowledged_at', 'resolved_at')
        }),
    )

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('title', 'report_type', 'report_format', 'created_at', 'generated_at', 'download_report')
    list_filter = ('report_type', 'report_format', 'created_at')
    search_fields = ('title', 'description')
    filter_horizontal = ('included_kpis',)
    readonly_fields = ('created_at', 'generated_at')
    fieldsets = (
        ('Report Information', {
            'fields': ('title', 'description', 'report_type', 'report_format')
        }),
        ('Time Range', {
            'fields': ('start_date', 'end_date')
        }),
        ('Filters', {
            'fields': ('included_kpis', 'event_types', 'departments')
        }),
        ('Generation Details', {
            'fields': ('generated_by', 'created_at', 'generated_at', 'file')
        }),
    )

    def download_report(self, obj):
        if obj.file:
            return format_html(
                '<a href="{}" class="button" target="_blank">Download</a>',
                obj.file.url
            )
        return "Not generated"
    download_report.short_description = 'Download'

@admin.register(DataAggregation)
class DataAggregationAdmin(admin.ModelAdmin):
    list_display = ('name', 'aggregation_type', 'time_period', 'value', 'count', 'last_updated')
    list_filter = ('aggregation_type', 'time_period')
    search_fields = ('name', 'description', 'department')
    readonly_fields = ('last_updated',)
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'aggregation_type', 'time_period')
        }),
        ('Source Configuration', {
            'fields': ('source_kpi', 'event_type', 'department')
        }),
        ('Time Range', {
            'fields': ('start_date', 'end_date')
        }),
        ('Results', {
            'fields': ('value', 'count', 'last_updated')
        }),
    )
