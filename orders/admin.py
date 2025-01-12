from django.contrib import admin
from django.utils.html import format_html
from .models import Order, OrderItem, Payment, MaterialRequirement

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['production_progress']
    fields = [
        'product', 'quantity', 'unit_price', 'produced_quantity',
        'in_production', 'production_progress', 'notes'
    ]

class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0
    fields = [
        'amount', 'payment_method', 'payment_date', 'status',
        'reference_number', 'receipt_number'
    ]

class MaterialRequirementInline(admin.TabularInline):
    model = MaterialRequirement
    extra = 0
    fields = [
        'material', 'required_quantity', 'allocated_quantity',
        'is_fully_allocated', 'remaining_quantity'
    ]
    readonly_fields = ['is_fully_allocated', 'remaining_quantity']

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'order_number', 'customer_name', 'order_date', 'required_date',
        'status_badge', 'priority_badge', 'payment_status', 'assigned_to'
    ]
    list_filter = ['status', 'priority', 'created_at', 'assigned_to']
    search_fields = ['order_number', 'customer_name', 'customer_email']
    inlines = [OrderItemInline, PaymentInline]
    readonly_fields = [
        'order_number', 'created_by', 'created_at', 'updated_at',
        'total_amount', 'paid_amount', 'balance', 'is_paid'
    ]
    fieldsets = (
        ('Order Information', {
            'fields': (
                'order_number', 'status', 'priority',
                ('created_at', 'updated_at')
            )
        }),
        ('Customer Information', {
            'fields': (
                'customer_name', 'customer_email', 'customer_phone',
                'customer_address'
            )
        }),
        ('Dates', {
            'fields': (
                ('order_date', 'required_date'),
                ('estimated_delivery', 'actual_delivery')
            )
        }),
        ('Financial', {
            'fields': (
                ('total_amount', 'paid_amount'),
                ('balance', 'is_paid')
            )
        }),
        ('Assignment', {
            'fields': (
                ('created_by', 'assigned_to'),
                'notes'
            )
        })
    )

    def status_badge(self, obj):
        colors = {
            'pending': 'orange',
            'confirmed': 'blue',
            'in_production': 'purple',
            'completed': 'green',
            'delivered': 'teal',
            'cancelled': 'red',
        }
        return format_html(
            '<span style="color: white; background-color: {}; padding: 3px 10px; '
            'border-radius: 3px;">{}</span>',
            colors.get(obj.status, 'gray'),
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    def priority_badge(self, obj):
        colors = {
            'low': 'green',
            'medium': 'blue',
            'high': 'orange',
            'urgent': 'red',
        }
        return format_html(
            '<span style="color: white; background-color: {}; padding: 3px 10px; '
            'border-radius: 3px;">{}</span>',
            colors.get(obj.priority, 'gray'),
            obj.get_priority_display()
        )
    priority_badge.short_description = 'Priority'

    def payment_status(self, obj):
        if obj.is_paid:
            color = 'green'
            text = 'Paid'
        elif obj.paid_amount > 0:
            color = 'orange'
            text = f'Partial ({obj.paid_amount}/{obj.total_amount})'
        else:
            color = 'red'
            text = 'Unpaid'
        return format_html(
            '<span style="color: {};">{}</span>',
            color, text
        )
    payment_status.short_description = 'Payment Status'

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = [
        'order', 'product', 'quantity', 'unit_price',
        'production_status', 'production_progress'
    ]
    list_filter = ['in_production', 'order__status']
    search_fields = ['order__order_number', 'product__name']
    inlines = [MaterialRequirementInline]
    readonly_fields = [
        'production_progress', 'total_price',
        'created_at', 'updated_at'
    ]

    def production_status(self, obj):
        if obj.production_completed:
            color = 'green'
            text = 'Completed'
        elif obj.in_production:
            color = 'blue'
            text = 'In Production'
        else:
            color = 'orange'
            text = 'Not Started'
        return format_html(
            '<span style="color: {};">{}</span>',
            color, text
        )
    production_status.short_description = 'Production Status'

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = [
        'order', 'amount', 'payment_method', 'payment_date',
        'status_badge', 'reference_number'
    ]
    list_filter = ['payment_method', 'status', 'payment_date']
    search_fields = [
        'order__order_number', 'reference_number',
        'receipt_number'
    ]
    readonly_fields = ['recorded_by', 'created_at', 'updated_at']

    def status_badge(self, obj):
        colors = {
            'pending': 'orange',
            'completed': 'green',
            'failed': 'red',
            'refunded': 'blue',
        }
        return format_html(
            '<span style="color: white; background-color: {}; padding: 3px 10px; '
            'border-radius: 3px;">{}</span>',
            colors.get(obj.status, 'gray'),
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'

@admin.register(MaterialRequirement)
class MaterialRequirementAdmin(admin.ModelAdmin):
    list_display = [
        'order_item', 'material', 'required_quantity',
        'allocated_quantity', 'allocation_status'
    ]
    list_filter = ['material', 'order_item__order__status']
    search_fields = [
        'order_item__order__order_number',
        'material__name'
    ]
    readonly_fields = [
        'is_fully_allocated', 'remaining_quantity',
        'created_at', 'updated_at'
    ]

    def allocation_status(self, obj):
        if obj.is_fully_allocated:
            color = 'green'
            text = 'Fully Allocated'
        elif obj.allocated_quantity > 0:
            color = 'orange'
            text = f'Partial ({obj.allocated_quantity}/{obj.required_quantity})'
        else:
            color = 'red'
            text = 'Not Allocated'
        return format_html(
            '<span style="color: {};">{}</span>',
            color, text
        )
    allocation_status.short_description = 'Allocation Status'
