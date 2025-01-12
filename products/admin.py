from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Category, Product, ProductSpecification,
    ProductComponent, ProductDocument
)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'parent', 'products_count', 'created_at']
    list_filter = ['parent']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']

    def products_count(self, obj):
        return obj.products.count()
    products_count.short_description = 'Products'

class ProductSpecificationInline(admin.TabularInline):
    model = ProductSpecification
    extra = 1

class ProductComponentInline(admin.TabularInline):
    model = ProductComponent
    extra = 1
    fk_name = 'product'
    autocomplete_fields = ['component']

class ProductDocumentInline(admin.TabularInline):
    model = ProductDocument
    extra = 1

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'sku', 'category', 'status', 'stock_status', 'unit_price', 'created_at']
    list_filter = ['status', 'category']
    search_fields = ['name', 'sku', 'description']
    readonly_fields = ['created_at', 'updated_at', 'discontinued_at']
    inlines = [
        ProductSpecificationInline,
        ProductComponentInline,
        ProductDocumentInline
    ]
    fieldsets = (
        (None, {
            'fields': ('name', 'sku', 'description', 'category', 'status')
        }),
        ('Pricing', {
            'fields': ('unit_price', 'cost_price')
        }),
        ('Inventory', {
            'fields': ('current_stock', 'min_stock_level', 'max_stock_level')
        }),
        ('Manufacturing', {
            'fields': ('manufacturing_lead_time', 'batch_size')
        }),
        ('Tracking', {
            'fields': ('created_at', 'updated_at', 'discontinued_at'),
            'classes': ('collapse',)
        })
    )

    def stock_status(self, obj):
        if obj.current_stock <= obj.min_stock_level:
            return format_html(
                '<span style="color: red;">Low Stock ({0})</span>',
                obj.current_stock
            )
        elif obj.current_stock >= obj.max_stock_level:
            return format_html(
                '<span style="color: blue;">High Stock ({0})</span>',
                obj.current_stock
            )
        return format_html(
            '<span style="color: green;">Normal ({0})</span>',
            obj.current_stock
        )
    stock_status.short_description = 'Stock Status'

@admin.register(ProductSpecification)
class ProductSpecificationAdmin(admin.ModelAdmin):
    list_display = ['product', 'attribute', 'value', 'unit']
    list_filter = ['product']
    search_fields = ['product__name', 'attribute', 'value']
    autocomplete_fields = ['product']

@admin.register(ProductComponent)
class ProductComponentAdmin(admin.ModelAdmin):
    list_display = ['product', 'component', 'quantity', 'optional']
    list_filter = ['optional', 'product', 'component']
    search_fields = ['product__name', 'component__name']
    autocomplete_fields = ['product', 'component']

@admin.register(ProductDocument)
class ProductDocumentAdmin(admin.ModelAdmin):
    list_display = ['product', 'title', 'document_type', 'version', 'created_at']
    list_filter = ['document_type', 'product']
    search_fields = ['product__name', 'title', 'notes']
    autocomplete_fields = ['product']
    readonly_fields = ['created_at', 'updated_at']
