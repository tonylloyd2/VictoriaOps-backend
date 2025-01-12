from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from django.db.models import Sum
from .models import (
    ProductionOrder, ProductionBatch, MaterialConsumption,
    QualityCheck, MaintenanceLog
)

@receiver(post_save, sender=ProductionBatch)
def update_order_progress(sender, instance, **kwargs):
    """Update production order progress when batch is updated"""
    order = instance.production_order
    total_produced = order.batches.aggregate(
        total=Sum('quantity_produced')
    )['total'] or 0
    
    # Update order status if completed
    if total_produced >= order.quantity and order.status == 'in_progress':
        order.status = 'completed'
        order.save()

@receiver(post_save, sender=MaterialConsumption)
def update_material_stock(sender, instance, **kwargs):
    """Update material stock levels when consumption is recorded"""
    material = instance.material
    material.quantity_available -= instance.quantity_used
    material.save()

@receiver(post_save, sender=QualityCheck)
def update_batch_quality(sender, instance, **kwargs):
    """Update batch quality status when check is performed"""
    batch = instance.batch
    checks = batch.quality_checks.all()
    
    # Update batch quality status
    if checks.filter(result='failed').exists():
        batch.quality_check_passed = False
    elif checks.filter(result='pending').exists():
        batch.quality_check_passed = None
    else:
        batch.quality_check_passed = True
    
    batch.save()

@receiver(post_save, sender=MaintenanceLog)
def update_production_line_status(sender, instance, created, **kwargs):
    """Update production line status when maintenance is logged"""
    line = instance.production_line
    
    if created:
        # Set line to maintenance mode when new maintenance is logged
        line.status = 'maintenance'
        line.save()
    elif instance.end_time:
        # Update line status and maintenance records when maintenance is completed
        line.status = 'active'
        line.last_maintenance = instance.end_time
        
        # Schedule next maintenance
        if instance.maintenance_type == 'preventive':
            # Schedule next maintenance in 30 days (adjust as needed)
            line.maintenance_schedule = instance.end_time + timezone.timedelta(days=30)
        
        line.save()

@receiver(pre_save, sender=ProductionOrder)
def validate_production_order(sender, instance, **kwargs):
    """Validate production order before saving"""
    if instance.status == 'in_progress':
        # Ensure production line is available
        if instance.production_line.status != 'active':
            raise ValueError('Production line is not active')
        
        # Check material availability
        requirements = instance.calculate_material_requirements()
        insufficient_materials = []
        
        for req in requirements:
            if req['material'].quantity_available < req['required_quantity']:
                insufficient_materials.append(
                    f"{req['material'].name} (Required: {req['required_quantity']}, "
                    f"Available: {req['material'].quantity_available})"
                )
        
        if insufficient_materials:
            raise ValueError(
                'Insufficient materials available: ' + 
                ', '.join(insufficient_materials)
            )
