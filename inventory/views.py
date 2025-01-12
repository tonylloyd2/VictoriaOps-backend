from django.shortcuts import render
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Sum, F, Q, Count
from django.utils import timezone
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
from .models import (
    Supplier, Warehouse, StorageLocation,
    RawMaterial, Stock, StockMovement
)
from .serializers import (
    SupplierSerializer, WarehouseSerializer, WarehouseDetailSerializer,
    StorageLocationSerializer, RawMaterialSerializer, RawMaterialDetailSerializer,
    StockSerializer, StockMovementSerializer
)
import logging

logger = logging.getLogger(__name__)

# Create your views here.

@extend_schema_view(
    list=extend_schema(
        summary="List all suppliers",
        description="Returns a list of all suppliers with optional filtering"
    ),
    create=extend_schema(
        summary="Create a new supplier",
        description="Create a new supplier with the provided data"
    ),
    retrieve=extend_schema(
        summary="Get a specific supplier",
        description="Returns the details of a specific supplier"
    ),
    update=extend_schema(
        summary="Update a supplier",
        description="Update all fields of a specific supplier"
    ),
    partial_update=extend_schema(
        summary="Partially update a supplier",
        description="Update specific fields of a supplier"
    ),
    destroy=extend_schema(
        summary="Delete a supplier",
        description="Delete a specific supplier"
    )
)
class SupplierViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing suppliers.
    """
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['name', 'code', 'contact_person', 'email']
    filterset_fields = ['active']

    def create(self, request, *args, **kwargs):
        logger.info(f"Creating new supplier: {request.data.get('name')}")
        try:
            response = super().create(request, *args, **kwargs)
            logger.info(f"Successfully created supplier with ID: {response.data.get('id')}")
            return response
        except Exception as e:
            logger.error(f"Error creating supplier: {str(e)}")
            raise

    def update(self, request, *args, **kwargs):
        logger.info(f"Updating supplier {kwargs.get('pk')}")
        try:
            response = super().update(request, *args, **kwargs)
            logger.info(f"Successfully updated supplier {kwargs.get('pk')}")
            return response
        except Exception as e:
            logger.error(f"Error updating supplier {kwargs.get('pk')}: {str(e)}")
            raise

@extend_schema_view(
    list=extend_schema(
        summary="List all warehouses",
        description="Returns a list of all warehouses with optional filtering"
    ),
    create=extend_schema(
        summary="Create a new warehouse",
        description="Create a new warehouse with the provided data"
    ),
    retrieve=extend_schema(
        summary="Get a specific warehouse",
        description="Returns the details of a specific warehouse"
    )
)
class WarehouseViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing warehouses.
    """
    queryset = Warehouse.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['name', 'code', 'location']
    filterset_fields = ['active']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return WarehouseDetailSerializer
        return WarehouseSerializer

    def get_queryset(self):
        logger.debug("Fetching warehouses queryset")
        queryset = Warehouse.objects.all()
        location = self.request.query_params.get('location', None)
        if location:
            logger.info(f"Filtering warehouses by location: {location}")
            queryset = queryset.filter(location__icontains=location)
        return queryset

    @extend_schema(
        summary="Get warehouse storage analysis",
        description="Returns detailed analysis of storage utilization for the warehouse",
        responses={200: {
            "type": "object",
            "properties": {
                "total_capacity": {"type": "number"},
                "total_utilized": {"type": "number"},
                "utilization_by_type": {
                    "type": "object",
                    "additionalProperties": {
                        "type": "object",
                        "properties": {
                            "capacity": {"type": "number"},
                            "utilized": {"type": "number"},
                            "location_count": {"type": "integer"}
                        }
                    }
                },
                "available_locations": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "location": {"type": "string"},
                            "type": {"type": "string"},
                            "available_space": {"type": "number"}
                        }
                    }
                }
            }
        }}
    )
    @action(detail=True)
    def storage_analysis(self, request, pk=None):
        """Get storage utilization analysis"""
        logger.info(f"Generating storage analysis for warehouse {pk}")
        try:
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

            logger.info(f"Successfully generated storage analysis for warehouse {pk}")
            return Response(analysis)
        except Exception as e:
            logger.error(f"Error generating storage analysis for warehouse {pk}: {str(e)}")
            return Response(
                {'error': 'Error generating storage analysis'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

@extend_schema_view(
    list=extend_schema(
        summary="List all storage locations",
        description="Returns a list of all storage locations with optional filtering"
    ),
    create=extend_schema(
        summary="Create a new storage location",
        description="Create a new storage location with the provided data"
    ),
    retrieve=extend_schema(
        summary="Get a specific storage location",
        description="Returns the details of a specific storage location"
    )
)
class StorageLocationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing storage locations.
    """
    queryset = StorageLocation.objects.all()
    serializer_class = StorageLocationSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['name', 'warehouse__name']
    filterset_fields = ['warehouse', 'location_type', 'temperature_controlled', 'active']

    def get_queryset(self):
        logger.debug("Fetching storage locations queryset")
        queryset = StorageLocation.objects.all()
        warehouse = self.request.query_params.get('warehouse', None)
        if warehouse:
            logger.info(f"Filtering storage locations by warehouse: {warehouse}")
            queryset = queryset.filter(warehouse__id=warehouse)
        return queryset

    @extend_schema(
        summary="Get list of stock in this location",
        description="Returns a list of stock items in the specified location"
    )
    @action(detail=True)
    def stock_list(self, request, pk=None):
        """Get list of stock in this location"""
        logger.info(f"Fetching stock list for location {pk}")
        try:
            location = self.get_object()
            stocks = location.stock_records.all()
            logger.info(f"Successfully fetched stock list for location {pk}")
            return Response(StockSerializer(stocks, many=True).data)
        except Exception as e:
            logger.error(f"Error fetching stock list for location {pk}: {str(e)}")
            return Response(
                {'error': 'Error fetching stock list'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

@extend_schema_view(
    list=extend_schema(
        summary="List all raw materials",
        description="Returns a list of all raw materials with optional filtering"
    ),
    create=extend_schema(
        summary="Create a new raw material",
        description="Create a new raw material with the provided data"
    ),
    retrieve=extend_schema(
        summary="Get a specific raw material",
        description="Returns the details of a specific raw material"
    )
)
class RawMaterialViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing raw materials.
    """
    queryset = RawMaterial.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['name', 'code', 'description']
    filterset_fields = ['active', 'unit']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return RawMaterialDetailSerializer
        return RawMaterialSerializer

    def get_queryset(self):
        logger.debug("Fetching raw materials queryset")
        queryset = RawMaterial.objects.all()
        category = self.request.query_params.get('category', None)
        if category:
            logger.info(f"Filtering raw materials by category: {category}")
            queryset = queryset.filter(category=category)
        return queryset

    @extend_schema(
        summary="Get stock analysis for the material",
        description="Returns analysis of stock levels for the specified material",
        parameters=[
            OpenApiParameter(
                name="start_date",
                description="Start date for analysis (YYYY-MM-DD)",
                required=False,
                type=str
            )
        ]
    )
    @action(detail=True)
    def stock_analysis(self, request, pk=None):
        """Get stock analysis for the material"""
        logger.info(f"Generating stock analysis for material {pk}")
        try:
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
            
            analysis = {
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
            }
            
            logger.info(f"Successfully generated stock analysis for material {pk}")
            return Response(analysis)
        except Exception as e:
            logger.error(f"Error generating stock analysis for material {pk}: {str(e)}")
            return Response(
                {'error': 'Error generating stock analysis'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

@extend_schema_view(
    list=extend_schema(
        summary="List all stock",
        description="Returns a list of all stock with optional filtering"
    ),
    create=extend_schema(
        summary="Create new stock",
        description="Create new stock with the provided data"
    ),
    retrieve=extend_schema(
        summary="Get specific stock",
        description="Returns the details of specific stock"
    )
)
class StockViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing stock.
    """
    queryset = Stock.objects.all()
    serializer_class = StockSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['material', 'location']

    def get_queryset(self):
        logger.debug("Fetching stock queryset")
        queryset = Stock.objects.all()
        material = self.request.query_params.get('material', None)
        location = self.request.query_params.get('location', None)

        if material:
            logger.info(f"Filtering stock by material: {material}")
            queryset = queryset.filter(material__id=material)
        if location:
            logger.info(f"Filtering stock by location: {location}")
            queryset = queryset.filter(storage_location__id=location)

        return queryset

    @extend_schema(
        summary="Get list of expiring stock",
        description="Returns a list of stock items that are expiring soon"
    )
    @action(detail=False)
    def expiring_soon(self, request):
        """Get list of stock expiring soon"""
        logger.info("Checking for expiring stock items")
        try:
            days = int(request.query_params.get('days', 90))
            expiry_date = timezone.now().date() + timezone.timedelta(days=days)
            
            stocks = self.queryset.filter(
                expiry_date__lte=expiry_date,
                expiry_date__gte=timezone.now().date()
            ).order_by('expiry_date')
            
            logger.info(f"Found {len(stocks)} expiring stock items")
            return Response(StockSerializer(stocks, many=True).data)
        except Exception as e:
            logger.error(f"Error checking expiring stock items: {str(e)}")
            return Response(
                {'error': 'Error checking expiring stock items'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @extend_schema(
        summary="Get list of low stock",
        description="Returns a list of stock items that are low"
    )
    @action(detail=False, methods=['get'])
    def low_stock(self, request):
        logger.info("Checking for low stock items")
        try:
            low_stock_items = Stock.objects.filter(
                Q(quantity_on_hand__lte=F('reorder_point')) |
                Q(quantity_on_hand__lte=F('minimum_stock_level'))
            )
            serializer = self.get_serializer(low_stock_items, many=True)
            logger.info(f"Found {len(serializer.data)} low stock items")
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error checking low stock items: {str(e)}")
            return Response(
                {'error': 'Error checking low stock items'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

@extend_schema_view(
    list=extend_schema(
        summary="List all stock movements",
        description="Returns a list of all stock movements with optional filtering",
        parameters=[
            OpenApiParameter(
                name="movement_type",
                description="Filter by movement type (receipt, issue, transfer)",
                required=False,
                type=str
            ),
            OpenApiParameter(
                name="material",
                description="Filter by material ID",
                required=False,
                type=int
            )
        ]
    )
)
class StockMovementViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing stock movements.
    """
    queryset = StockMovement.objects.all()
    serializer_class = StockMovementSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['reference_number', 'batch_number', 'notes']
    filterset_fields = ['material', 'movement_type', 'source_location', 'destination_location']

    def create(self, request, *args, **kwargs):
        logger.info(f"Creating new stock movement: {request.data}")
        try:
            response = super().create(request, *args, **kwargs)
            logger.info(f"Successfully created stock movement with ID: {response.data.get('id')}")
            return response
        except Exception as e:
            logger.error(f"Error creating stock movement: {str(e)}")
            raise

    def get_queryset(self):
        logger.debug("Fetching stock movements queryset")
        queryset = StockMovement.objects.all()
        stock = self.request.query_params.get('stock', None)
        movement_type = self.request.query_params.get('movement_type', None)

        if stock:
            logger.info(f"Filtering stock movements by stock: {stock}")
            queryset = queryset.filter(stock__id=stock)
        if movement_type:
            logger.info(f"Filtering stock movements by type: {movement_type}")
            queryset = queryset.filter(movement_type=movement_type)

        return queryset

    @extend_schema(
        summary="Get movement analysis",
        description="Returns analysis of stock movements over time",
        parameters=[
            OpenApiParameter(
                name="start_date",
                description="Start date for analysis (YYYY-MM-DD)",
                required=False,
                type=str
            )
        ]
    )
    @action(detail=False)
    def movement_analysis(self, request):
        """Get movement analysis"""
        logger.info("Generating movement analysis")
        try:
            start_date = request.query_params.get(
                'start_date',
                (timezone.now() - timezone.timedelta(days=90)).date()
            )
            
            movements = self.queryset.filter(created_at__date__gte=start_date)
            
            analysis = {
                'total_movements': movements.count(),
                'by_type': movements.values('movement_type').annotate(
                    count=Count('id'),
                    total_quantity=Sum('quantity')
                ),
                'by_material': movements.values('material__name').annotate(
                    count=Count('id'),
                    total_quantity=Sum('quantity')
                ).order_by('-total_quantity')[:10]
            }
            
            logger.info("Successfully generated movement analysis")
            return Response(analysis)
        except Exception as e:
            logger.error(f"Error generating movement analysis: {str(e)}")
            return Response(
                {'error': 'Error generating movement analysis'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
