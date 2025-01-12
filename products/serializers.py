from rest_framework import serializers
from .models import (
    Category, Product, ProductSpecification,
    ProductComponent, ProductDocument
)

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

class CategoryDetailSerializer(serializers.ModelSerializer):
    subcategories = serializers.SerializerMethodField()
    products_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = '__all__'

    def get_subcategories(self, obj):
        return CategorySerializer(obj.subcategories.all(), many=True).data

    def get_products_count(self, obj):
        return obj.products.count()

class ProductSpecificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductSpecification
        fields = '__all__'

class ProductComponentSerializer(serializers.ModelSerializer):
    component_name = serializers.CharField(source='component.name', read_only=True)
    component_sku = serializers.CharField(source='component.sku', read_only=True)

    class Meta:
        model = ProductComponent
        fields = '__all__'

class ProductDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductDocument
        fields = '__all__'

class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = Product
        fields = '__all__'

class ProductDetailSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    specifications = ProductSpecificationSerializer(many=True, read_only=True)
    components = ProductComponentSerializer(many=True, read_only=True)
    documents = ProductDocumentSerializer(many=True, read_only=True)
    used_in = ProductComponentSerializer(many=True, read_only=True)
    stock_status = serializers.SerializerMethodField()
    profit_margin = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = '__all__'

    def get_stock_status(self, obj):
        if obj.current_stock <= obj.min_stock_level:
            return 'low'
        elif obj.current_stock >= obj.max_stock_level:
            return 'high'
        return 'normal'

    def get_profit_margin(self, obj):
        if obj.unit_price and obj.cost_price:
            margin = ((obj.unit_price - obj.cost_price) / obj.unit_price) * 100
            return round(margin, 2)
        return None
