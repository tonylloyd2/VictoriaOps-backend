from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from django.db.models import Sum
from .models import Product, ProductComponent

@receiver(post_save, sender=Product)
def handle_product_discontinuation(sender, instance, **kwargs):
    """Handle product discontinuation tasks"""
    if instance.status == 'discontinued' and instance.discontinued_at:
        # Update components that use this product
        affected_products = instance.used_in.all()
        for usage in affected_products:
            if not usage.optional:
                # Mark dependent products as discontinued
                product = usage.product
                if product.status != 'discontinued':
                    product.status = 'discontinued'
                    product.discontinued_at = timezone.now()
                    product.save()

@receiver(post_save, sender=ProductComponent)
def update_product_cost(sender, instance, **kwargs):
    """Update product cost when components change"""
    product = instance.product
    
    # Calculate total component cost
    total_component_cost = product.components.aggregate(
        total=Sum(
            'quantity' * F('component__cost_price'),
            output_field=models.DecimalField()
        )
    )['total'] or 0
    
    # Add manufacturing cost (assumed 20% of component cost)
    manufacturing_cost = total_component_cost * 0.2
    
    # Update product cost
    product.cost_price = total_component_cost + manufacturing_cost
    product.save()
