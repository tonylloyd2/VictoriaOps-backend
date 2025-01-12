from django.shortcuts import render
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Sum, F, Count
from django.utils import timezone
from .models import (
    Category, Product, ProductSpecification,
    ProductComponent, ProductDocument
)
from .serializers import (
    CategorySerializer, CategoryDetailSerializer,
    ProductSerializer, ProductDetailSerializer,
    ProductSpecificationSerializer, ProductComponentSerializer,
    ProductDocumentSerializer
)

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['name', 'description']
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return CategoryDetailSerializer
        return CategorySerializer
    
    @action(detail=True)
    def products(self, request, pk=None):
        """Get all products in this category and its subcategories"""
        category = self.get_object()
        subcategories = category.subcategories.all()
        products = Product.objects.filter(
            Q(category=category) | Q(category__in=subcategories)
        )
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['name', 'sku', 'description']
    filterset_fields = ['category', 'status']
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ProductDetailSerializer
        return ProductSerializer
    
    @action(detail=True, methods=['post'])
    def discontinue(self, request, pk=None):
        """Discontinue a product"""
        product = self.get_object()
        product.discontinue()
        return Response(ProductDetailSerializer(product).data)
    
    @action(detail=True)
    def stock_analysis(self, request, pk=None):
        """Get stock analysis for the product"""
        product = self.get_object()
        
        # Calculate stock turnover
        start_date = request.query_params.get(
            'start_date',
            (timezone.now() - timezone.timedelta(days=90)).date()
        )
        
        production_quantity = product.production_batches.filter(
            end_time__date__gte=start_date
        ).aggregate(
            total=Sum('quantity_produced')
        )['total'] or 0
        
        stock_turnover = production_quantity / (product.current_stock or 1)
        
        return Response({
            'current_stock': product.current_stock,
            'min_stock_level': product.min_stock_level,
            'max_stock_level': product.max_stock_level,
            'stock_status': 'low' if product.current_stock <= product.min_stock_level else 'high' if product.current_stock >= product.max_stock_level else 'normal',
            'production_quantity_90d': production_quantity,
            'stock_turnover_90d': round(stock_turnover, 2),
            'days_until_stockout': round(product.current_stock / (production_quantity/90)) if production_quantity > 0 else None
        })
    
    @action(detail=True)
    def bom(self, request, pk=None):
        """Get Bill of Materials for the product"""
        product = self.get_object()
        components = product.components.select_related('component').all()
        
        return Response({
            'product': ProductSerializer(product).data,
            'components': ProductComponentSerializer(components, many=True).data,
            'total_cost': sum(
                comp.quantity * comp.component.cost_price
                for comp in components
            )
        })

class ProductSpecificationViewSet(viewsets.ModelViewSet):
    queryset = ProductSpecification.objects.all()
    serializer_class = ProductSpecificationSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['product']

class ProductComponentViewSet(viewsets.ModelViewSet):
    queryset = ProductComponent.objects.all()
    serializer_class = ProductComponentSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['product', 'component', 'optional']
    
    @action(detail=False)
    def component_usage(self, request):
        """Get usage analysis of components"""
        components = ProductComponent.objects.values(
            'component'
        ).annotate(
            usage_count=Count('product'),
            total_quantity=Sum('quantity')
        ).order_by('-usage_count')
        
        return Response(components)

class ProductDocumentViewSet(viewsets.ModelViewSet):
    queryset = ProductDocument.objects.all()
    serializer_class = ProductDocumentSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['title', 'notes']
    filterset_fields = ['product', 'document_type']
