from rest_framework import serializers
from django.utils import timezone
from .models import (
    ProductionLine, ProductionOrder, ProductionBatch,
    MaterialConsumption, QualityCheck, MaintenanceLog
)

class ProductionLineSerializer(serializers.ModelSerializer):
    maintenance_status = serializers.SerializerMethodField()
    current_order = serializers.SerializerMethodField()
    efficiency = serializers.SerializerMethodField()

    class Meta:
        model = ProductionLine
        fields = list(['id', 'name', 'capacity_per_hour', 'maintenance_schedule', 'supervisor', 'created_at', 'updated_at', 'maintenance_status', 'current_order', 'efficiency'])
        read_only_fields = ['created_at', 'updated_at']

    def get_maintenance_status(self, obj):
        if not obj.maintenance_schedule:
            return 'Not Scheduled'
        
        if obj.maintenance_schedule < timezone.now():
            return 'Overdue'
            
        days_until = (obj.maintenance_schedule - timezone.now()).days
        if days_until <= 7:
            return f'Due in {days_until} days'
            
        return 'Scheduled'

    def get_current_order(self, obj):
        current_order = obj.production_orders.filter(
            status='in_progress'
        ).first()
        if current_order:
            return {
                'order_number': current_order.order_number,
                'product': current_order.product.name,
                'quantity': current_order.quantity,
                'progress': self._calculate_progress(current_order)
            }
        return None

    def get_efficiency(self, obj):
        """Calculate production line efficiency"""
        recent_batches = ProductionBatch.objects.filter(
            production_order__production_line=obj,
            end_time__isnull=False
        ).order_by('-end_time')[:10]
        
        if not recent_batches:
            return None
            
        total_time = sum(
            (batch.end_time - batch.start_time).total_seconds()
            for batch in recent_batches
        )
        total_produced = sum(batch.quantity_produced for batch in recent_batches)
        
        if total_time > 0:
            actual_rate = (total_produced / total_time) * 3600  # per hour
            return (actual_rate / obj.capacity_per_hour) * 100
        return None

    def _calculate_progress(self, order):
        total_produced = sum(
            batch.quantity_produced for batch in order.batches.all()
        )
        if order.quantity:
            return (total_produced / order.quantity) * 100
        return 0

class MaterialConsumptionSerializer(serializers.ModelSerializer):
    material_name = serializers.CharField(source='material.name', read_only=True)
    efficiency = serializers.SerializerMethodField()
    recorded_by_name = serializers.CharField(source='recorded_by.get_full_name', read_only=True)

    class Meta:
        model = MaterialConsumption
        fields = list(['id', 'batch', 'material', 'quantity_used', 'wastage', 'recorded_by', 'created_at', 'updated_at', 'material_name', 'efficiency', 'recorded_by_name'])
        read_only_fields = ['created_at', 'updated_at']

    def get_efficiency(self, obj):
        if obj.quantity_used:
            return ((obj.quantity_used - obj.wastage) / obj.quantity_used) * 100
        return None

class QualityCheckSerializer(serializers.ModelSerializer):
    checked_by_name = serializers.CharField(source='checked_by.get_full_name', read_only=True)
    batch_number = serializers.CharField(source='batch.batch_number', read_only=True)

    class Meta:
        model = QualityCheck
        fields = list(['id', 'batch', 'checked_by', 'inspection_date', 'passed', 'created_at', 'updated_at', 'checked_by_name', 'batch_number'])
        read_only_fields = ['created_at', 'updated_at']

class ProductionBatchSerializer(serializers.ModelSerializer):
    material_consumptions = MaterialConsumptionSerializer(many=True, read_only=True)
    quality_checks = QualityCheckSerializer(many=True, read_only=True)
    operator_name = serializers.CharField(source='operator.get_full_name', read_only=True)
    efficiency = serializers.SerializerMethodField()

    class Meta:
        model = ProductionBatch
        fields = list(['id', 'production_order', 'batch_number', 'start_time', 'end_time', 'quantity_produced', 'defect_count', 'operator', 'created_at', 'updated_at', 'material_consumptions', 'quality_checks', 'operator_name', 'efficiency'])
        read_only_fields = ['created_at', 'updated_at']

    def get_efficiency(self, obj):
        """Calculate batch production efficiency"""
        if obj.end_time and obj.start_time:
            duration = (obj.end_time - obj.start_time).total_seconds() / 3600  # hours
            if duration > 0:
                return (obj.quantity_produced / duration) / obj.production_order.production_line.capacity_per_hour * 100
        return None

class ProductionOrderSerializer(serializers.ModelSerializer):
    batches = ProductionBatchSerializer(many=True, read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    assigned_to_name = serializers.CharField(source='assigned_to.get_full_name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    progress = serializers.SerializerMethodField()
    material_requirements = serializers.SerializerMethodField()

    class Meta:
        model = ProductionOrder
        fields = list(['id', 'production_line', 'order_number', 'product', 'quantity', 'status', 'start_date', 'end_date', 'assigned_to', 'created_by', 'created_at', 'updated_at', 'completed_at', 'batches', 'product_name', 'assigned_to_name', 'created_by_name', 'progress', 'material_requirements'])
        read_only_fields = ['created_at', 'updated_at', 'completed_at']

    def get_progress(self, obj):
        total_produced = sum(batch.quantity_produced for batch in obj.batches.all())
        if obj.quantity:
            return (total_produced / obj.quantity) * 100
        return 0

    def get_material_requirements(self, obj):
        return obj.calculate_material_requirements()

class MaintenanceLogSerializer(serializers.ModelSerializer):
    production_line_name = serializers.CharField(source='production_line.name', read_only=True)
    performed_by_name = serializers.CharField(source='performed_by.get_full_name', read_only=True)
    verified_by_name = serializers.CharField(source='verified_by.get_full_name', read_only=True)
    duration = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()

    class Meta:
        model = MaintenanceLog
        fields = list(['id', 'production_line', 'maintenance_type', 'start_time', 'end_time', 'performed_by', 'verified_by', 'created_at', 'updated_at', 'production_line_name', 'performed_by_name', 'verified_by_name', 'duration', 'status'])
        read_only_fields = ['created_at', 'updated_at']

    def get_duration(self, obj):
        if obj.end_time:
            duration = obj.end_time - obj.start_time
            return duration.total_seconds() / 3600  # Return hours
        return None

    def get_status(self, obj):
        if not obj.end_time:
            return 'In Progress'
        if obj.verified_by:
            return 'Verified'
        return 'Completed'

# Additional Serializers for nested representations
class ProductionLineDetailSerializer(ProductionLineSerializer):
    """Extended production line serializer with related data"""
    recent_maintenance = serializers.SerializerMethodField()
    current_orders = serializers.SerializerMethodField()
    performance_metrics = serializers.SerializerMethodField()

    class Meta(ProductionLineSerializer.Meta):
        fields = list(ProductionLineSerializer.Meta.fields) + ['recent_maintenance', 'current_orders', 'performance_metrics']

    def get_recent_maintenance(self, obj):
        recent_logs = obj.maintenance_logs.order_by('-start_time')[:5]
        return MaintenanceLogSerializer(recent_logs, many=True).data

    def get_current_orders(self, obj):
        current_orders = obj.production_orders.filter(
            status__in=['scheduled', 'in_progress']
        ).order_by('priority', 'start_date')[:5]
        return ProductionOrderSerializer(current_orders, many=True).data

    def get_performance_metrics(self, obj):
        recent_batches = ProductionBatch.objects.filter(
            production_order__production_line=obj,
            end_time__isnull=False
        ).order_by('-end_time')[:50]
        
        if not recent_batches:
            return None
        
        total_time = sum(
            (batch.end_time - batch.start_time).total_seconds()
            for batch in recent_batches
        )
        total_produced = sum(batch.quantity_produced for batch in recent_batches)
        defect_rate = sum(batch.defect_count for batch in recent_batches) / total_produced if total_produced else 0
        
        return {
            'efficiency': (total_produced / total_time * 3600) / obj.capacity_per_hour * 100 if total_time > 0 else None,
            'defect_rate': defect_rate * 100,
            'utilization': total_time / (len(recent_batches) * 24 * 3600) * 100  # Assuming 24-hour operation
        }

class ProductionOrderDetailSerializer(ProductionOrderSerializer):
    """Extended production order serializer with quality metrics"""
    quality_metrics = serializers.SerializerMethodField()
    material_efficiency = serializers.SerializerMethodField()
    timeline = serializers.SerializerMethodField()

    class Meta(ProductionOrderSerializer.Meta):
        fields = list(ProductionOrderSerializer.Meta.fields) + ['quality_metrics', 'material_efficiency', 'timeline']

    def get_quality_metrics(self, obj):
        batches = obj.batches.all()
        total_produced = sum(batch.quantity_produced for batch in batches)
        total_defects = sum(batch.defect_count for batch in batches)
        
        return {
            'defect_rate': (total_defects / total_produced * 100) if total_produced else 0,
            'quality_pass_rate': len([b for b in batches if b.quality_check_passed]) / len(batches) * 100 if batches else 0,
            'total_defects': total_defects
        }

    def get_material_efficiency(self, obj):
        consumptions = MaterialConsumption.objects.filter(batch__production_order=obj)
        efficiencies = []
        
        for consumption in consumptions:
            if consumption.quantity_used:
                efficiency = ((consumption.quantity_used - consumption.wastage) / consumption.quantity_used) * 100
                efficiencies.append({
                    'material': consumption.material.name,
                    'efficiency': efficiency,
                    'wastage': consumption.wastage
                })
        
        return efficiencies

    def get_timeline(self, obj):
        events = []
        
        # Add order events
        events.append({
            'time': obj.created_at,
            'event': 'Order Created',
            'details': f'Created by {obj.created_by.get_full_name() if obj.created_by else "System"}'
        })
        
        # Add batch events
        for batch in obj.batches.all():
            events.append({
                'time': batch.start_time,
                'event': 'Batch Started',
                'details': f'Batch {batch.batch_number}'
            })
            if batch.end_time:
                events.append({
                    'time': batch.end_time,
                    'event': 'Batch Completed',
                    'details': f'Produced {batch.quantity_produced} units'
                })
        
        # Sort events by time
        events.sort(key=lambda x: x['time'])
        return events
