from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Supplier, Warehouse, StorageLocation,
    RawMaterial, Stock, StockMovement
)

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'contact_person', 'email', 'phone', 'active']
    list_filter = ['active']
    search_fields = ['name', 'code', 'contact_person', 'email']
    readonly_fields = ['created_at', 'updated_at']

class StorageLocationInline(admin.TabularInline):
    model = StorageLocation
    extra = 1

@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'location', 'capacity', 'utilization', 'manager', 'active']
    list_filter = ['active']
    search_fields = ['name', 'code', 'location']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [StorageLocationInline]

    def utilization(self, obj):
        util = obj.get_current_utilization()
        color = 'green'
        if util > 90:
            color = 'red'
        elif util > 70:
            color = 'orange'
        return format_html(
            '<span style="color: {}">{:.1f}%</span>',
            color, util
        )
    utilization.short_description = 'Utilization'

@admin.register(StorageLocation)
class StorageLocationAdmin(admin.ModelAdmin):
    list_display = ['name', 'warehouse', 'location_type', 'capacity', 'utilization', 'temperature_controlled', 'active']
    list_filter = ['warehouse', 'location_type', 'temperature_controlled', 'active']
    search_fields = ['name', 'warehouse__name']

    def utilization(self, obj):
        util = (obj.current_volume / obj.capacity * 100) if obj.capacity else 0
        color = 'green'
        if util > 90:
            color = 'red'
        elif util > 70:
            color = 'orange'
        return format_html(
            '<span style="color: {}">{:.1f}%</span>',
            color, util
        )
    utilization.short_description = 'Utilization'

class StockInline(admin.TabularInline):
    model = Stock
    extra = 1
    readonly_fields = ['created_at', 'updated_at']

@admin.register(RawMaterial)
class RawMaterialAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'unit', 'current_stock', 'stock_status', 'unit_price', 'active']
    list_filter = ['active', 'unit']
    search_fields = ['name', 'code', 'description']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [StockInline]
    fieldsets = (
        (None, {
            'fields': ('name', 'code', 'description', 'unit', 'active')
        }),
        ('Stock Management', {
            'fields': ('minimum_stock', 'maximum_stock', 'reorder_point', 'lead_time')
        }),
        ('Pricing & Storage', {
            'fields': ('unit_price', 'volume_per_unit')
        }),
        ('Notes & Tracking', {
            'fields': ('notes', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

    def stock_status(self, obj):
        current = obj.current_stock
        if current <= obj.minimum_stock:
            return format_html(
                '<span style="color: red;">Low Stock ({0})</span>',
                current
            )
        elif current >= obj.maximum_stock:
            return format_html(
                '<span style="color: blue;">Overstocked ({0})</span>',
                current
            )
        elif current <= obj.reorder_point:
            return format_html(
                '<span style="color: orange;">Reorder ({0})</span>',
                current
            )
        return format_html(
            '<span style="color: green;">Normal ({0})</span>',
            current
        )
    stock_status.short_description = 'Stock Status'

@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ['material', 'location', 'quantity', 'batch_number', 'expiry_date']
    list_filter = ['location', 'material', 'expiry_date']
    search_fields = ['material__name', 'batch_number']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ['reference_number', 'movement_type', 'material', 'quantity', 'source_location', 'destination_location', 'created_at']
    list_filter = ['movement_type', 'material', 'source_location', 'destination_location']
    search_fields = ['reference_number', 'batch_number', 'material__name']
    readonly_fields = ['created_at']
    fieldsets = (
        (None, {
            'fields': ('movement_type', 'material', 'quantity', 'batch_number', 'reference_number')
        }),
        ('Locations', {
            'fields': ('source_location', 'destination_location')
        }),
        ('Additional Information', {
            'fields': ('performed_by', 'notes', 'created_at')
        })
    )
