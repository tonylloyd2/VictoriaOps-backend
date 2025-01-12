from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from products.models import Product
from inventory.models import RawMaterial

User = get_user_model()

class Order(models.Model):
    ORDER_STATUS = (
        ('pending', _('Pending')),
        ('confirmed', _('Confirmed')),
        ('in_production', _('In Production')),
        ('completed', _('Completed')),
        ('delivered', _('Delivered')),
        ('cancelled', _('Cancelled')),
    )

    PRIORITY_CHOICES = (
        ('low', _('Low')),
        ('medium', _('Medium')),
        ('high', _('High')),
        ('urgent', _('Urgent')),
    )

    order_number = models.CharField(max_length=50, unique=True)
    customer_name = models.CharField(max_length=255)
    customer_email = models.EmailField()
    customer_phone = models.CharField(max_length=20)
    customer_address = models.TextField()
    
    order_date = models.DateTimeField(auto_now_add=True)
    required_date = models.DateTimeField()
    estimated_delivery = models.DateTimeField(null=True, blank=True)
    actual_delivery = models.DateTimeField(null=True, blank=True)
    
    status = models.CharField(max_length=20, choices=ORDER_STATUS, default='pending')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, 
        null=True, related_name='created_orders'
    )
    assigned_to = models.ForeignKey(
        User, on_delete=models.SET_NULL, 
        null=True, blank=True, related_name='assigned_orders'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('Order')
        verbose_name_plural = _('Orders')

    def __str__(self):
        return f"Order #{self.order_number} - {self.customer_name}"

    @property
    def is_paid(self):
        return self.paid_amount >= self.total_amount

    @property
    def balance(self):
        return self.total_amount - self.paid_amount

class OrderItem(models.Model):
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE,
        related_name='items'
    )
    product = models.ForeignKey(
        Product, on_delete=models.PROTECT,
        related_name='order_items'
    )
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Production tracking
    produced_quantity = models.PositiveIntegerField(default=0)
    in_production = models.BooleanField(default=False)
    production_started = models.DateTimeField(null=True, blank=True)
    production_completed = models.DateTimeField(null=True, blank=True)
    
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Order Item')
        verbose_name_plural = _('Order Items')

    def __str__(self):
        return f"{self.product.name} ({self.quantity} units)"

    @property
    def total_price(self):
        return self.quantity * self.unit_price

    @property
    def production_progress(self):
        if self.quantity == 0:
            return 0
        return (self.produced_quantity / self.quantity) * 100

class Payment(models.Model):
    PAYMENT_METHOD = (
        ('cash', _('Cash')),
        ('bank_transfer', _('Bank Transfer')),
        ('credit_card', _('Credit Card')),
        ('mobile_money', _('Mobile Money')),
        ('cheque', _('Cheque')),
    )

    PAYMENT_STATUS = (
        ('pending', _('Pending')),
        ('completed', _('Completed')),
        ('failed', _('Failed')),
        ('refunded', _('Refunded')),
    )

    order = models.ForeignKey(
        Order, on_delete=models.CASCADE,
        related_name='payments'
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD)
    payment_date = models.DateTimeField()
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending')
    
    reference_number = models.CharField(max_length=100, blank=True)
    receipt_number = models.CharField(max_length=100, blank=True)
    
    notes = models.TextField(blank=True)
    recorded_by = models.ForeignKey(
        User, on_delete=models.SET_NULL,
        null=True, related_name='recorded_payments'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-payment_date']
        verbose_name = _('Payment')
        verbose_name_plural = _('Payments')

    def __str__(self):
        return f"Payment #{self.id} - {self.amount} ({self.payment_method})"

class MaterialRequirement(models.Model):
    order_item = models.ForeignKey(
        OrderItem, on_delete=models.CASCADE,
        related_name='material_requirements'
    )
    material = models.ForeignKey(
        RawMaterial, on_delete=models.PROTECT,
        related_name='order_requirements'
    )
    required_quantity = models.DecimalField(max_digits=10, decimal_places=2)
    allocated_quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Material Requirement')
        verbose_name_plural = _('Material Requirements')

    def __str__(self):
        return f"{self.material.name} for {self.order_item}"

    @property
    def is_fully_allocated(self):
        return self.allocated_quantity >= self.required_quantity

    @property
    def remaining_quantity(self):
        return self.required_quantity - self.allocated_quantity
