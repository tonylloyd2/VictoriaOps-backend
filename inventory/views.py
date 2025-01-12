from django.shortcuts import render
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Sum, F, Q, Count
from django.utils import timezone
from .models import (
    Supplier, Warehouse, StorageLocation,
    RawMaterial, Stock, StockMovement
)
from .serializers import (
    SupplierSerializer, WarehouseSerializer, WarehouseDetailSerializer,
    StorageLocationSerializer, RawMaterialSerializer, RawMaterialDetailSerializer,
    StockSerializer, StockMovementSerializer
)

# Create your views here.

class SupplierViewSet(viewsets.ModelViewSet):
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['name', 'code', 'contact_person', 'email']
    filterset_fields = ['active']

class WarehouseViewSet(viewsets.ModelViewSet):
    queryset = Warehouse.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['name', 'code', 'location']
    filterset_fields = ['active']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return WarehouseDetailSerializer
        return WarehouseSerializer

    @action(detail=True)
    def storage_analysis(self, request, pk=None):
        """Get storage utilization analysis"""
        warehouse = self.get_object()
        locations = warehouse.storage_locations.all()

        analysis = {
            'total_capacity': warehouse.capacity,
            'total_utilized': sum(loc.current_volume for loc in locations),
            'utilization_by_type': {},
            'available_locations': []
        }

        # Analyze utilization by location type
        for loc in locations:
            if loc.location_type not in analysis['utilization_by_type']:
                analysis['utilization_by_type'][loc.location_type] = {
                    'capacity': 0,
                    'utilized': 0,
                    'location_count': 0
                }
            
            type_stats = analysis['utilization_by_type'][loc.location_type]
            type_stats['capacity'] += loc.capacity
            type_stats['utilized'] += loc.current_volume
            type_stats['location_count'] += 1

            # Check for available space
            if loc.current_volume < loc.capacity:
                analysis['available_locations'].append({
                    'location': loc.name,
                    'type': loc.location_type,
                    'available_space': loc.capacity - loc.current_volume
                })

        return Response(analysis)

class StorageLocationViewSet(viewsets.ModelViewSet):
    queryset = StorageLocation.objects.all()
    serializer_class = StorageLocationSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['name', 'warehouse__name']
    filterset_fields = ['warehouse', 'location_type', 'temperature_controlled', 'active']

    @action(detail=True)
    def stock_list(self, request, pk=None):
        """Get list of stock in this location"""
        location = self.get_object()
        stocks = location.stock_records.all()
        return Response(StockSerializer(stocks, many=True).data)

class RawMaterialViewSet(viewsets.ModelViewSet):
    queryset = RawMaterial.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['name', 'code', 'description']
    filterset_fields = ['active', 'unit']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return RawMaterialDetailSerializer
        return RawMaterialSerializer

    @action(detail=True)
    def stock_analysis(self, request, pk=None):
        """Get stock analysis for the material"""
        material = self.get_object()
        
        # Calculate consumption rate
        start_date = request.query_params.get(
            'start_date',
            (timezone.now() - timezone.timedelta(days=90)).date()
        )
        
        consumption = material.movements.filter(
            movement_type='issue',
            created_at__date__gte=start_date
        ).aggregate(
            total=Sum('quantity')
        )['total'] or 0
        
        daily_consumption = consumption / 90  # Average daily consumption
        
        return Response({
            'current_stock': material.current_stock,
            'stock_value': material.stock_value,
            'min_stock': material.minimum_stock,
            'max_stock': material.maximum_stock,
            'reorder_point': material.reorder_point,
            'consumption_90d': consumption,
            'avg_daily_consumption': round(daily_consumption, 2),
            'days_until_reorder': round(
                (material.current_stock - material.reorder_point) / daily_consumption
            ) if daily_consumption > 0 else None,
            'days_of_stock': round(
                material.current_stock / daily_consumption
            ) if daily_consumption > 0 else None
        })

class StockViewSet(viewsets.ModelViewSet):
    queryset = Stock.objects.all()
    serializer_class = StockSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['material', 'location']

    @action(detail=False)
    def expiring_soon(self, request):
        """Get list of stock expiring soon"""
        days = int(request.query_params.get('days', 90))
        expiry_date = timezone.now().date() + timezone.timedelta(days=days)
        
        stocks = self.queryset.filter(
            expiry_date__lte=expiry_date,
            expiry_date__gte=timezone.now().date()
        ).order_by('expiry_date')
        
        return Response(StockSerializer(stocks, many=True).data)

class StockMovementViewSet(viewsets.ModelViewSet):
    queryset = StockMovement.objects.all()
    serializer_class = StockMovementSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['reference_number', 'batch_number', 'notes']
    filterset_fields = ['material', 'movement_type', 'source_location', 'destination_location']

    @action(detail=False)
    def movement_analysis(self, request):
        """Get movement analysis"""
        start_date = request.query_params.get(
            'start_date',
            (timezone.now() - timezone.timedelta(days=90)).date()
        )
        
        movements = self.queryset.filter(
            created_at__date__gte=start_date
        )
        
        analysis = {
            'total_movements': movements.count(),
            'by_type': movements.values(
                'movement_type'
            ).annotate(
                count=Count('id'),
                total_quantity=Sum('quantity')
            ),
            'by_material': movements.values(
                'material__name'
            ).annotate(
                count=Count('id'),
                total_quantity=Sum('quantity')
            ).order_by('-total_quantity')[:10]
        }
        
        return Response(analysis)
