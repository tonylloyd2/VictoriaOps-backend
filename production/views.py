from django.shortcuts import render
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Sum, F, Q
from django.utils import timezone
from .models import (
    ProductionLine, ProductionOrder, ProductionBatch,
    MaterialConsumption, QualityCheck, MaintenanceLog
)
from .serializers import (
    ProductionLineSerializer, ProductionLineDetailSerializer,
    ProductionOrderSerializer, ProductionOrderDetailSerializer,
    ProductionBatchSerializer, MaterialConsumptionSerializer,
    QualityCheckSerializer, MaintenanceLogSerializer
)

class ProductionLineViewSet(viewsets.ModelViewSet):
    queryset = ProductionLine.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['name', 'description']
    filterset_fields = ['status']
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ProductionLineDetailSerializer
        return ProductionLineSerializer
    
    @action(detail=True)
    def schedule(self, request, pk=None):
        """Get production schedule for the line"""
        line = self.get_object()
        scheduled_orders = line.production_orders.filter(
            status__in=['scheduled', 'in_progress']
        ).order_by('start_date')
        
        return Response({
            'current_order': ProductionOrderSerializer(
                scheduled_orders.filter(status='in_progress').first()
            ).data,
            'upcoming_orders': ProductionOrderSerializer(
                scheduled_orders.filter(status='scheduled'),
                many=True
            ).data
        })
    
    @action(detail=True)
    def performance(self, request, pk=None):
        """Get performance metrics for the line"""
        line = self.get_object()
        start_date = request.query_params.get(
            'start_date',
            timezone.now().date() - timezone.timedelta(days=30)
        )
        
        batches = ProductionBatch.objects.filter(
            production_order__production_line=line,
            start_time__date__gte=start_date
        )
        
        total_produced = batches.aggregate(
            total=Sum('quantity_produced')
        )['total'] or 0
        total_defects = batches.aggregate(
            total=Sum('defect_count')
        )['total'] or 0
        
        return Response({
            'total_produced': total_produced,
            'defect_rate': (total_defects / total_produced * 100) if total_produced else 0,
            'efficiency': line.get_efficiency(),
            'maintenance_status': line.get_maintenance_status()
        })

class ProductionOrderViewSet(viewsets.ModelViewSet):
    queryset = ProductionOrder.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['order_number', 'product__name', 'notes']
    filterset_fields = ['status', 'priority', 'production_line']
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ProductionOrderDetailSerializer
        return ProductionOrderSerializer
    
    @action(detail=True, methods=['post'])
    def start_production(self, request, pk=None):
        """Start production for an order"""
        order = self.get_object()
        
        if order.status != 'scheduled':
            return Response(
                {'error': 'Order must be scheduled to start production'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if production line is available
        if order.production_line.status != 'active':
            return Response(
                {'error': 'Production line is not active'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check material availability
        requirements = order.calculate_material_requirements()
        insufficient_materials = []
        
        for req in requirements:
            if req['material'].quantity_available < req['required_quantity']:
                insufficient_materials.append({
                    'material': req['material'].name,
                    'required': req['required_quantity'],
                    'available': req['material'].quantity_available
                })
        
        if insufficient_materials:
            return Response({
                'error': 'Insufficient materials',
                'details': insufficient_materials
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Start production
        order.status = 'in_progress'
        order.save()
        
        # Create initial batch
        batch = ProductionBatch.objects.create(
            production_order=order,
            batch_number=f"B-{order.order_number}-1",
            start_time=timezone.now()
        )
        
        return Response({
            'message': 'Production started',
            'order': ProductionOrderSerializer(order).data,
            'batch': ProductionBatchSerializer(batch).data
        })
    
    @action(detail=True, methods=['post'])
    def complete_production(self, request, pk=None):
        """Complete production for an order"""
        order = self.get_object()
        
        if order.status != 'in_progress':
            return Response(
                {'error': 'Order must be in progress to complete'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Complete any active batches
        active_batches = order.batches.filter(end_time__isnull=True)
        for batch in active_batches:
            batch.end_time = timezone.now()
            batch.save()
        
        # Update order status
        order.status = 'completed'
        order.save()
        
        return Response(ProductionOrderDetailSerializer(order).data)

class ProductionBatchViewSet(viewsets.ModelViewSet):
    queryset = ProductionBatch.objects.all()
    serializer_class = ProductionBatchSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['batch_number', 'production_order__order_number']
    filterset_fields = ['quality_check_passed']
    
    @action(detail=True, methods=['post'])
    def record_production(self, request, pk=None):
        """Record production quantity and quality"""
        batch = self.get_object()
        quantity = request.data.get('quantity')
        defects = request.data.get('defects', 0)
        
        if not quantity:
            return Response(
                {'error': 'Quantity is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        batch.quantity_produced = quantity
        batch.defect_count = defects
        batch.save()
        
        return Response(ProductionBatchSerializer(batch).data)
    
    @action(detail=True, methods=['post'])
    def complete_batch(self, request, pk=None):
        """Complete a production batch"""
        batch = self.get_object()
        
        if batch.end_time:
            return Response(
                {'error': 'Batch is already completed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        batch.end_time = timezone.now()
        batch.save()
        
        # Check if this was the last batch for the order
        order = batch.production_order
        if not order.batches.filter(end_time__isnull=True).exists():
            if order.status == 'in_progress':
                order.status = 'completed'
                order.save()
        
        return Response(ProductionBatchSerializer(batch).data)

class MaterialConsumptionViewSet(viewsets.ModelViewSet):
    queryset = MaterialConsumption.objects.all()
    serializer_class = MaterialConsumptionSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['material', 'batch']
    
    @action(detail=False)
    def consumption_report(self, request):
        """Generate material consumption report"""
        start_date = request.query_params.get(
            'start_date',
            timezone.now().date() - timezone.timedelta(days=30)
        )
        
        consumptions = self.queryset.filter(
            recorded_at__date__gte=start_date
        )
        
        report = consumptions.values(
            'material__name'
        ).annotate(
            total_used=Sum('quantity_used'),
            total_waste=Sum('wastage'),
            efficiency=100 * (1 - Sum('wastage') / Sum('quantity_used'))
        )
        
        return Response(list(report))

class QualityCheckViewSet(viewsets.ModelViewSet):
    queryset = QualityCheck.objects.all()
    serializer_class = QualityCheckSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['parameter', 'batch__batch_number']
    filterset_fields = ['result', 'batch']
    
    @action(detail=False)
    def quality_metrics(self, request):
        """Generate quality metrics report"""
        start_date = request.query_params.get(
            'start_date',
            timezone.now().date() - timezone.timedelta(days=30)
        )
        
        checks = self.queryset.filter(
            check_time__date__gte=start_date
        )
        
        metrics = {
            'total_checks': checks.count(),
            'pass_rate': checks.filter(
                result='passed'
            ).count() / checks.count() * 100 if checks.exists() else 0,
            'parameters': checks.values(
                'parameter'
            ).annotate(
                total=Sum('id'),
                passed=Sum('id', filter=Q(result='passed')),
                failed=Sum('id', filter=Q(result='failed'))
            )
        }
        
        return Response(metrics)

class MaintenanceLogViewSet(viewsets.ModelViewSet):
    queryset = MaintenanceLog.objects.all()
    serializer_class = MaintenanceLogSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['production_line__name', 'description']
    filterset_fields = ['maintenance_type', 'production_line']
    
    @action(detail=True, methods=['post'])
    def complete_maintenance(self, request, pk=None):
        """Complete a maintenance task"""
        log = self.get_object()
        
        if log.end_time:
            return Response(
                {'error': 'Maintenance is already completed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        log.end_time = timezone.now()
        log.save()
        
        # Update production line status
        line = log.production_line
        line.status = 'active'
        line.last_maintenance = timezone.now()
        line.save()
        
        return Response(MaintenanceLogSerializer(log).data)
    
    @action(detail=False)
    def maintenance_schedule(self, request):
        """Get maintenance schedule"""
        upcoming = self.queryset.filter(
            end_time__isnull=True
        ).order_by('start_time')
        
        overdue = ProductionLine.objects.filter(
            maintenance_schedule__lt=timezone.now()
        )
        
        return Response({
            'upcoming_maintenance': MaintenanceLogSerializer(
                upcoming,
                many=True
            ).data,
            'overdue_maintenance': ProductionLineSerializer(
                overdue,
                many=True
            ).data
        })
