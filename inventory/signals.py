from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from django.db.models import Sum
from .models import Stock, StockMovement, StorageLocation

@receiver(pre_save, sender=Stock)
def validate_stock_location(sender, instance, **kwargs):
    """Validate stock location has enough space"""
    if not instance.pk:  # New stock
        required_volume = instance.quantity * instance.material.volume_per_unit
        if not instance.location.is_available(required_volume):
            raise ValidationError(
                f"Location {instance.location} does not have enough space for "
                f"{instance.quantity} units of {instance.material}"
            )

@receiver(post_save, sender=Stock)
def update_location_volume(sender, instance, created, **kwargs):
    """Update storage location volume when stock changes"""
    location = instance.location
    total_volume = location.stock_records.aggregate(
        total=Sum(
            F('quantity') * F('material__volume_per_unit')
        )
    )['total'] or 0
    
    location.current_volume = total_volume
    location.save()

@receiver(post_delete, sender=Stock)
def handle_stock_deletion(sender, instance, **kwargs):
    """Update location volume when stock is deleted"""
    location = instance.location
    total_volume = location.stock_records.exclude(
        pk=instance.pk
    ).aggregate(
        total=Sum(
            F('quantity') * F('material__volume_per_unit')
        )
    )['total'] or 0
    
    location.current_volume = total_volume
    location.save()

@receiver(pre_save, sender=StockMovement)
def validate_stock_movement(sender, instance, **kwargs):
    """Validate stock movement"""
    if instance.movement_type == 'transfer':
        # Check source location has enough stock
        try:
            source_stock = Stock.objects.get(
                material=instance.material,
                location=instance.source_location,
                batch_number=instance.batch_number
            )
            if source_stock.quantity < instance.quantity:
                raise ValidationError(
                    f"Insufficient stock at {instance.source_location}. "
                    f"Available: {source_stock.quantity}, Required: {instance.quantity}"
                )
        except Stock.DoesNotExist:
            raise ValidationError(
                f"No stock found for {instance.material} at {instance.source_location} "
                f"with batch number {instance.batch_number}"
            )
        
        # Check destination location has enough space
        required_volume = instance.quantity * instance.material.volume_per_unit
        if not instance.destination_location.is_available(required_volume):
            raise ValidationError(
                f"Destination location {instance.destination_location} does not have "
                f"enough space for {instance.quantity} units"
            )
    
    elif instance.movement_type == 'issue':
        # Check source location has enough stock
        try:
            source_stock = Stock.objects.get(
                material=instance.material,
                location=instance.source_location,
                batch_number=instance.batch_number
            )
            if source_stock.quantity < instance.quantity:
                raise ValidationError(
                    f"Insufficient stock at {instance.source_location}. "
                    f"Available: {source_stock.quantity}, Required: {instance.quantity}"
                )
        except Stock.DoesNotExist:
            raise ValidationError(
                f"No stock found for {instance.material} at {instance.source_location} "
                f"with batch number {instance.batch_number}"
            )
    
    elif instance.movement_type == 'receipt':
        # Check destination location has enough space
        required_volume = instance.quantity * instance.material.volume_per_unit
        if not instance.destination_location.is_available(required_volume):
            raise ValidationError(
                f"Destination location {instance.destination_location} does not have "
                f"enough space for {instance.quantity} units"
            )
