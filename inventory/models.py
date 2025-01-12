from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from django.conf import settings

class Supplier(models.Model):
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=50, unique=True)
    contact_person = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    address = models.TextField()
    active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.code})"

class Warehouse(models.Model):
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=50, unique=True)
    location = models.CharField(max_length=200)
    capacity = models.PositiveIntegerField(help_text="Storage capacity in cubic meters")
    manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='managed_warehouses'
    )
    active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.code})"

    def get_current_utilization(self):
        """Calculate current warehouse utilization"""
        total_volume = sum(
            location.current_volume for location in self.storage_locations.all()
        )
        return (total_volume / self.capacity) * 100 if self.capacity else 0

class StorageLocation(models.Model):
    LOCATION_TYPES = [
        ('shelf', 'Shelf'),
        ('rack', 'Rack'),
        ('bin', 'Bin'),
        ('floor', 'Floor Space'),
        ('cold', 'Cold Storage'),
    ]

    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='storage_locations')
    name = models.CharField(max_length=100)
    location_type = models.CharField(max_length=20, choices=LOCATION_TYPES)
    capacity = models.PositiveIntegerField(help_text="Storage capacity in cubic meters")
    current_volume = models.PositiveIntegerField(default=0, help_text="Current volume occupied in cubic meters")
    temperature_controlled = models.BooleanField(default=False)
    temperature_range = models.CharField(max_length=50, blank=True, help_text="e.g., '2-8°C'")
    active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.warehouse.name} - {self.name} ({self.location_type})"

    def is_available(self, required_volume):
        """Check if location has enough space"""
        return (self.capacity - self.current_volume) >= required_volume

class RawMaterial(models.Model):
    UNIT_CHOICES = [
        ('kg', 'Kilograms'),
        ('l', 'Liters'),
        ('m', 'Meters'),
        ('pcs', 'Pieces'),
        ('m2', 'Square Meters'),
        ('m3', 'Cubic Meters'),
    ]

    name = models.CharField(max_length=200)
    code = models.CharField(max_length=50, unique=True)
    description = models.TextField()
    unit = models.CharField(max_length=10, choices=UNIT_CHOICES)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    minimum_stock = models.PositiveIntegerField(default=0)
    maximum_stock = models.PositiveIntegerField()
    reorder_point = models.PositiveIntegerField()
    lead_time = models.PositiveIntegerField(help_text="Lead time in days")
    
    # Dimensions for storage calculations
    volume_per_unit = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        help_text="Volume per unit in cubic meters",
        validators=[MinValueValidator(0)]
    )
    
    active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.code})"

    @property
    def current_stock(self):
        """Get current stock level across all locations"""
        return sum(stock.quantity for stock in self.stock_records.all())

    @property
    def stock_value(self):
        """Calculate total value of current stock"""
        return self.current_stock * self.unit_price

class Stock(models.Model):
    material = models.ForeignKey(RawMaterial, on_delete=models.CASCADE, related_name='stock_records')
    location = models.ForeignKey(StorageLocation, on_delete=models.CASCADE, related_name='stock_records')
    quantity = models.PositiveIntegerField()
    batch_number = models.CharField(max_length=50)
    expiry_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['material', 'location', 'batch_number']

    def __str__(self):
        return f"{self.material.name} at {self.location.name} - {self.quantity} {self.material.unit}"

    def save(self, *args, **kwargs):
        if not self.pk:  # New stock record
            # Update storage location volume
            volume = self.quantity * self.material.volume_per_unit
            self.location.current_volume += volume
            self.location.save()
        super().save(*args, **kwargs)

class StockMovement(models.Model):
    MOVEMENT_TYPES = [
        ('receipt', 'Receipt'),
        ('issue', 'Issue'),
        ('transfer', 'Transfer'),
        ('adjustment', 'Adjustment'),
        ('return', 'Return'),
    ]

    material = models.ForeignKey(RawMaterial, on_delete=models.CASCADE, related_name='movements')
    source_location = models.ForeignKey(
        StorageLocation,
        on_delete=models.SET_NULL,
        null=True,
        related_name='outgoing_movements'
    )
    destination_location = models.ForeignKey(
        StorageLocation,
        on_delete=models.SET_NULL,
        null=True,
        related_name='incoming_movements'
    )
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPES)
    quantity = models.PositiveIntegerField()
    batch_number = models.CharField(max_length=50)
    reference_number = models.CharField(max_length=50, unique=True)
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.movement_type}: {self.material.name} - {self.quantity} {self.material.unit}"

    def save(self, *args, **kwargs):
        if not self.pk:  # New movement
            if self.movement_type == 'transfer':
                # Update source location
                source_stock = Stock.objects.get(
                    material=self.material,
                    location=self.source_location,
                    batch_number=self.batch_number
                )
                source_stock.quantity -= self.quantity
                if source_stock.quantity == 0:
                    source_stock.delete()
                else:
                    source_stock.save()

                # Update destination location
                dest_stock, created = Stock.objects.get_or_create(
                    material=self.material,
                    location=self.destination_location,
                    batch_number=self.batch_number,
                    defaults={'quantity': 0}
                )
                dest_stock.quantity += self.quantity
                dest_stock.save()

            elif self.movement_type == 'receipt':
                stock, created = Stock.objects.get_or_create(
                    material=self.material,
                    location=self.destination_location,
                    batch_number=self.batch_number,
                    defaults={'quantity': 0}
                )
                stock.quantity += self.quantity
                stock.save()

            elif self.movement_type == 'issue':
                stock = Stock.objects.get(
                    material=self.material,
                    location=self.source_location,
                    batch_number=self.batch_number
                )
                stock.quantity -= self.quantity
                if stock.quantity == 0:
                    stock.delete()
                else:
                    stock.save()

        super().save(*args, **kwargs)
