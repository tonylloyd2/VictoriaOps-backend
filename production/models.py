from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.contrib.auth import get_user_model
from products.models import Product  # Updated import statement
from inventory.models import RawMaterial

User = get_user_model()

class ProductionLine(models.Model):
    """Model for managing production lines in the factory"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    capacity_per_hour = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Production capacity per hour"
    )
    status = models.CharField(
        max_length=20,
        choices=[
            ('active', 'Active'),
            ('maintenance', 'Under Maintenance'),
            ('inactive', 'Inactive')
        ],
        default='active'
    )
    maintenance_schedule = models.DateTimeField(null=True, blank=True)
    last_maintenance = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class ProductionOrder(models.Model):
    """Model for managing production orders"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('on_hold', 'On Hold')
    ]

    order_number = models.CharField(max_length=50, unique=True)
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name='production_orders'
    )
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    production_line = models.ForeignKey(
        ProductionLine,
        on_delete=models.PROTECT,
        related_name='production_orders'
    )
    
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft'
    )
    
    priority = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        default=3,
        help_text="1 (Lowest) to 5 (Highest)"
    )
    
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='assigned_productions'
    )
    notes = models.TextField(blank=True)
    
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_productions'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"PO-{self.order_number} - {self.product.name}"

    def calculate_material_requirements(self):
        """Calculate required raw materials based on product recipe"""
        requirements = []
        for recipe_item in self.product.recipe.items.all():
            required_quantity = recipe_item.quantity * self.quantity
            requirements.append({
                'material': recipe_item.material,
                'required_quantity': required_quantity
            })
        return requirements

class ProductionBatch(models.Model):
    """Model for tracking production batches"""
    batch_number = models.CharField(max_length=50, unique=True)
    production_order = models.ForeignKey(
        ProductionOrder,
        on_delete=models.PROTECT,
        related_name='batches'
    )
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)
    quantity_produced = models.DecimalField(max_digits=10, decimal_places=2)
    
    defect_count = models.IntegerField(default=0)
    quality_check_passed = models.BooleanField(default=False)
    quality_notes = models.TextField(blank=True)
    
    operator = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='operated_batches'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Batch {self.batch_number}"

class MaterialConsumption(models.Model):
    """Model for tracking material consumption in production"""
    batch = models.ForeignKey(
        ProductionBatch,
        on_delete=models.PROTECT,
        related_name='material_consumptions'
    )
    material = models.ForeignKey(
        RawMaterial,
        on_delete=models.PROTECT,
        related_name='consumption_records'
    )
    quantity_used = models.DecimalField(max_digits=10, decimal_places=2)
    wastage = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Amount of material wasted during production"
    )
    
    recorded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True
    )
    recorded_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.material.name} - {self.batch.batch_number}"

class QualityCheck(models.Model):
    """Model for quality control checks during production"""
    RESULT_CHOICES = [
        ('passed', 'Passed'),
        ('failed', 'Failed'),
        ('pending', 'Pending Review')
    ]

    batch = models.ForeignKey(
        ProductionBatch,
        on_delete=models.CASCADE,
        related_name='quality_checks'
    )
    check_time = models.DateTimeField(default=timezone.now)
    parameter = models.CharField(max_length=100)
    expected_value = models.CharField(max_length=100)
    actual_value = models.CharField(max_length=100)
    result = models.CharField(
        max_length=20,
        choices=RESULT_CHOICES,
        default='pending'
    )
    
    checked_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True
    )
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"QC-{self.parameter} for {self.batch.batch_number}"

class MaintenanceLog(models.Model):
    """Model for tracking production line maintenance"""
    MAINTENANCE_TYPES = [
        ('preventive', 'Preventive'),
        ('corrective', 'Corrective'),
        ('breakdown', 'Breakdown')
    ]

    production_line = models.ForeignKey(
        ProductionLine,
        on_delete=models.CASCADE,
        related_name='maintenance_logs'
    )
    maintenance_type = models.CharField(
        max_length=20,
        choices=MAINTENANCE_TYPES
    )
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)
    description = models.TextField()
    
    cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    spare_parts_used = models.TextField(blank=True)
    
    performed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='maintenance_tasks'
    )
    verified_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='verified_maintenance'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.maintenance_type} - {self.production_line.name}"
