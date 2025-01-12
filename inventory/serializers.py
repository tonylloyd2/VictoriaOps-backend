from rest_framework import serializers
from .models import (
    Supplier, Warehouse, StorageLocation,
    RawMaterial, Stock, StockMovement
)

class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = '__all__'

class StorageLocationSerializer(serializers.ModelSerializer):
    warehouse_name = serializers.CharField(source='warehouse.name', read_only=True)
    utilization = serializers.SerializerMethodField()

    class Meta:
        model = StorageLocation
        fields = '__all__'

    def get_utilization(self, obj):
        return (obj.current_volume / obj.capacity * 100) if obj.capacity else 0

class WarehouseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Warehouse
        fields = '__all__'

class WarehouseDetailSerializer(serializers.ModelSerializer):
    storage_locations = StorageLocationSerializer(many=True, read_only=True)
    utilization = serializers.SerializerMethodField()
    manager_name = serializers.CharField(source='manager.get_full_name', read_only=True)

    class Meta:
        model = Warehouse
        fields = '__all__'

    def get_utilization(self, obj):
        return obj.get_current_utilization()

class RawMaterialSerializer(serializers.ModelSerializer):
    current_stock = serializers.IntegerField(read_only=True)
    stock_value = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = RawMaterial
        fields = '__all__'

class RawMaterialDetailSerializer(serializers.ModelSerializer):
    current_stock = serializers.IntegerField(read_only=True)
    stock_value = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    stock_by_location = serializers.SerializerMethodField()
    recent_movements = serializers.SerializerMethodField()

    class Meta:
        model = RawMaterial
        fields = '__all__'

    def get_stock_by_location(self, obj):
        return [
            {
                'location': str(stock.location),
                'quantity': stock.quantity,
                'batch_number': stock.batch_number,
                'expiry_date': stock.expiry_date
            }
            for stock in obj.stock_records.all()
        ]

    def get_recent_movements(self, obj):
        return [
            {
                'date': movement.created_at,
                'type': movement.movement_type,
                'quantity': movement.quantity,
                'reference': movement.reference_number
            }
            for movement in obj.movements.order_by('-created_at')[:5]
        ]

class StockSerializer(serializers.ModelSerializer):
    material_name = serializers.CharField(source='material.name', read_only=True)
    location_name = serializers.CharField(source='location.name', read_only=True)
    unit = serializers.CharField(source='material.unit', read_only=True)

    class Meta:
        model = Stock
        fields = '__all__'

class StockMovementSerializer(serializers.ModelSerializer):
    material_name = serializers.CharField(source='material.name', read_only=True)
    source_location_name = serializers.CharField(source='source_location.name', read_only=True)
    destination_location_name = serializers.CharField(source='destination_location.name', read_only=True)
    performed_by_name = serializers.CharField(source='performed_by.get_full_name', read_only=True)

    class Meta:
        model = StockMovement
        fields = '__all__'
