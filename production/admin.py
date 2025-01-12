from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import (
    ProductionLine, ProductionOrder, ProductionBatch,
    MaterialConsumption, QualityCheck, MaintenanceLog
)

@admin.register(ProductionLine)
class ProductionLineAdmin(admin.ModelAdmin):
    list_display = ('name', 'status', 'capacity_per_hour', 'maintenance_status', 'last_maintenance')
    list_filter = ('status', 'maintenance_schedule')
    search_fields = ('name', 'description')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'capacity_per_hour', 'status')
        }),
        ('Maintenance', {
            'fields': ('maintenance_schedule', 'last_maintenance')
        }),
    )
    
    def maintenance_status(self, obj):
        if not obj.maintenance_schedule:
            return format_html(
                '<span style="color: gray;">Not Scheduled</span>'
            )
        
        if obj.maintenance_schedule < timezone.now():
            return format_html(
                '<span style="color: red;">Overdue</span>'
            )
            
        days_until = (obj.maintenance_schedule - timezone.now()).days
        if days_until <= 7:
            return format_html(
                '<span style="color: orange;">Due in {} days</span>',
                days_until
            )
            
        return format_html(
            '<span style="color: green;">Scheduled</span>'
        )

class MaterialConsumptionInline(admin.TabularInline):
    model = MaterialConsumption
    extra = 1
    fields = ('material', 'quantity_used', 'wastage', 'recorded_by', 'notes')
    readonly_fields = ('recorded_by',)

    def save_model(self, request, obj, form, change):
        if not obj.recorded_by:
            obj.recorded_by = request.user
        super().save_model(request, obj, form, change)

class QualityCheckInline(admin.TabularInline):
    model = QualityCheck
    extra = 1
    fields = ('parameter', 'expected_value', 'actual_value', 'result', 'checked_by', 'notes')
    readonly_fields = ('checked_by',)

@admin.register(ProductionOrder)
class ProductionOrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'product', 'quantity', 'status', 'priority', 'progress')
    list_filter = ('status', 'priority', 'start_date')
    search_fields = ('order_number', 'product__name', 'notes')
    date_hierarchy = 'start_date'
    
    fieldsets = (
        ('Order Information', {
            'fields': (
                'order_number',
                ('product', 'quantity'),
                'production_line',
                ('start_date', 'end_date')
            )
        }),
        ('Status & Assignment', {
            'fields': (
                ('status', 'priority'),
                ('assigned_to', 'created_by'),
                'notes'
            )
        }),
    )
    readonly_fields = ('created_by',)
    
    def save_model(self, request, obj, form, change):
        if not obj.created_by:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    def progress(self, obj):
        total_produced = sum(
            batch.quantity_produced for batch in obj.batches.all()
        )
        if obj.quantity:
            percentage = (total_produced / obj.quantity) * 100
            if percentage >= 100:
                color = 'green'
            elif percentage >= 75:
                color = 'blue'
            elif percentage >= 50:
                color = 'orange'
            else:
                color = 'red'
            
            return format_html(
                '<span style="color: {};">{:.1f}%</span>',
                color,
                percentage
            )
        return '0%'

@admin.register(ProductionBatch)
class ProductionBatchAdmin(admin.ModelAdmin):
    list_display = ('batch_number', 'production_order_link', 'quantity_produced', 'quality_status', 'operator')
    list_filter = ('quality_check_passed', 'start_time')
    search_fields = ('batch_number', 'production_order__order_number')
    inlines = [MaterialConsumptionInline, QualityCheckInline]
    
    fieldsets = (
        ('Batch Information', {
            'fields': (
                'batch_number',
                'production_order',
                ('start_time', 'end_time'),
                'quantity_produced'
            )
        }),
        ('Quality Control', {
            'fields': (
                ('defect_count', 'quality_check_passed'),
                'quality_notes',
                'operator'
            )
        }),
    )
    
    def production_order_link(self, obj):
        url = reverse('admin:production_productionorder_change', args=[obj.production_order.id])
        return format_html('<a href="{}">{}</a>', url, obj.production_order.order_number)
    production_order_link.short_description = 'Production Order'
    
    def quality_status(self, obj):
        if not obj.quality_check_passed:
            return format_html(
                '<span style="color: red;">Failed</span>'
            )
        if obj.defect_count > 0:
            return format_html(
                '<span style="color: orange;">Passed with Defects ({})</span>',
                obj.defect_count
            )
        return format_html(
            '<span style="color: green;">Passed</span>'
        )

@admin.register(MaterialConsumption)
class MaterialConsumptionAdmin(admin.ModelAdmin):
    list_display = ('material', 'batch_link', 'quantity_used', 'wastage', 'efficiency')
    list_filter = ('material', 'recorded_at')
    search_fields = ('batch__batch_number', 'material__name', 'notes')
    date_hierarchy = 'recorded_at'
    
    def batch_link(self, obj):
        url = reverse('admin:production_productionbatch_change', args=[obj.batch.id])
        return format_html('<a href="{}">{}</a>', url, obj.batch.batch_number)
    batch_link.short_description = 'Batch'
    
    def efficiency(self, obj):
        if obj.quantity_used:
            efficiency = ((obj.quantity_used - obj.wastage) / obj.quantity_used) * 100
            if efficiency >= 95:
                color = 'green'
            elif efficiency >= 90:
                color = 'blue'
            elif efficiency >= 85:
                color = 'orange'
            else:
                color = 'red'
            
            return format_html(
                '<span style="color: {};">{:.1f}%</span>',
                color,
                efficiency
            )
        return 'N/A'

@admin.register(QualityCheck)
class QualityCheckAdmin(admin.ModelAdmin):
    list_display = ('parameter', 'batch_link', 'result', 'check_time', 'checked_by')
    list_filter = ('result', 'check_time')
    search_fields = ('parameter', 'batch__batch_number', 'notes')
    date_hierarchy = 'check_time'
    
    def batch_link(self, obj):
        url = reverse('admin:production_productionbatch_change', args=[obj.batch.id])
        return format_html('<a href="{}">{}</a>', url, obj.batch.batch_number)
    batch_link.short_description = 'Batch'

@admin.register(MaintenanceLog)
class MaintenanceLogAdmin(admin.ModelAdmin):
    list_display = ('production_line', 'maintenance_type', 'duration', 'cost', 'status')
    list_filter = ('maintenance_type', 'start_time', 'production_line')
    search_fields = ('production_line__name', 'description', 'spare_parts_used')
    date_hierarchy = 'start_time'
    
    fieldsets = (
        ('Maintenance Information', {
            'fields': (
                'production_line',
                'maintenance_type',
                ('start_time', 'end_time'),
                'description'
            )
        }),
        ('Cost & Parts', {
            'fields': (
                'cost',
                'spare_parts_used'
            )
        }),
        ('Verification', {
            'fields': (
                'performed_by',
                'verified_by'
            )
        }),
    )
    
    def duration(self, obj):
        if obj.end_time:
            duration = obj.end_time - obj.start_time
            hours = duration.total_seconds() / 3600
            return f"{hours:.1f} hours"
        return "In Progress"
    
    def status(self, obj):
        if not obj.end_time:
            return format_html(
                '<span style="color: blue;">In Progress</span>'
            )
        if obj.verified_by:
            return format_html(
                '<span style="color: green;">Verified</span>'
            )
        return format_html(
            '<span style="color: orange;">Completed</span>'
        )
