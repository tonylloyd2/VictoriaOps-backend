from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='subcategories')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def __str__(self):
        return self.name

class Product(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('discontinued', 'Discontinued'),
        ('in_development', 'In Development'),
    ]

    name = models.CharField(max_length=200)
    sku = models.CharField(max_length=50, unique=True)
    description = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='products')
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    # Inventory management
    min_stock_level = models.PositiveIntegerField(default=0)
    max_stock_level = models.PositiveIntegerField(default=1000)
    current_stock = models.PositiveIntegerField(default=0)
    
    # Manufacturing details
    manufacturing_lead_time = models.PositiveIntegerField(help_text='Manufacturing lead time in days', default=1)
    batch_size = models.PositiveIntegerField(help_text='Standard batch size for production', default=1)
    
    # Tracking
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    discontinued_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.sku})"

    def discontinue(self):
        self.status = 'discontinued'
        self.discontinued_at = timezone.now()
        self.save()

class ProductSpecification(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='specifications')
    attribute = models.CharField(max_length=100)
    value = models.CharField(max_length=255)
    unit = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['product', 'attribute']
        ordering = ['attribute']

    def __str__(self):
        return f"{self.product.name} - {self.attribute}: {self.value}{self.unit}"

class ProductComponent(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='components')
    component = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='used_in')
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    optional = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['product', 'component']
        ordering = ['product', 'component']

    def __str__(self):
        return f"{self.product.name} - {self.component.name} ({self.quantity})"

class ProductDocument(models.Model):
    DOCUMENT_TYPES = [
        ('manual', 'User Manual'),
        ('spec_sheet', 'Specification Sheet'),
        ('safety_doc', 'Safety Document'),
        ('quality_cert', 'Quality Certificate'),
        ('other', 'Other'),
    ]

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='documents')
    title = models.CharField(max_length=200)
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES)
    file = models.FileField(upload_to='product_documents/')
    version = models.CharField(max_length=50)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ['product', 'title', 'version']

    def __str__(self):
        return f"{self.product.name} - {self.title} (v{self.version})"
