from rest_framework import serializers
from .models import Order, OrderItem, Payment, MaterialRequirement

class MaterialRequirementSerializer(serializers.ModelSerializer):
    material_name = serializers.CharField(source='material.name', read_only=True)
    
    class Meta:
        model = MaterialRequirement
        fields = [
            'id', 'material', 'material_name', 'required_quantity',
            'allocated_quantity', 'is_fully_allocated', 'remaining_quantity',
            'notes'
        ]
        read_only_fields = ['allocated_quantity']

class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    total_price = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True
    )
    production_progress = serializers.FloatField(read_only=True)
    material_requirements = MaterialRequirementSerializer(many=True, read_only=True)
    
    class Meta:
        model = OrderItem
        fields = [
            'id', 'order', 'product', 'product_name', 'quantity',
            'unit_price', 'total_price', 'produced_quantity',
            'in_production', 'production_started', 'production_completed',
            'production_progress', 'material_requirements', 'notes'
        ]
        read_only_fields = [
            'produced_quantity', 'in_production',
            'production_started', 'production_completed'
        ]

class PaymentSerializer(serializers.ModelSerializer):
    recorded_by_name = serializers.CharField(
        source='recorded_by.get_full_name',
        read_only=True
    )
    
    class Meta:
        model = Payment
        fields = [
            'id', 'order', 'amount', 'payment_method', 'payment_date',
            'status', 'reference_number', 'receipt_number', 'notes',
            'recorded_by', 'recorded_by_name'
        ]
        read_only_fields = ['recorded_by']

    def create(self, validated_data):
        validated_data['recorded_by'] = self.context['request'].user
        return super().create(validated_data)

class OrderListSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    priority_display = serializers.CharField(
        source='get_priority_display',
        read_only=True
    )
    is_paid = serializers.BooleanField(read_only=True)
    balance = serializers.DecimalField(
        max_digits=10, decimal_places=2,
        read_only=True
    )
    
    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'customer_name', 'order_date',
            'required_date', 'status', 'status_display', 'priority',
            'priority_display', 'total_amount', 'paid_amount',
            'is_paid', 'balance'
        ]

class OrderDetailSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    payments = PaymentSerializer(many=True, read_only=True)
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    priority_display = serializers.CharField(
        source='get_priority_display',
        read_only=True
    )
    created_by_name = serializers.CharField(
        source='created_by.get_full_name',
        read_only=True
    )
    assigned_to_name = serializers.CharField(
        source='assigned_to.get_full_name',
        read_only=True
    )
    is_paid = serializers.BooleanField(read_only=True)
    balance = serializers.DecimalField(
        max_digits=10, decimal_places=2,
        read_only=True
    )
    
    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'customer_name', 'customer_email',
            'customer_phone', 'customer_address', 'order_date',
            'required_date', 'estimated_delivery', 'actual_delivery',
            'status', 'status_display', 'priority', 'priority_display',
            'total_amount', 'paid_amount', 'is_paid', 'balance',
            'notes', 'created_by', 'created_by_name', 'assigned_to',
            'assigned_to_name', 'items', 'payments', 'created_at',
            'updated_at'
        ]
        read_only_fields = [
            'order_number', 'total_amount', 'paid_amount',
            'created_by', 'created_at', 'updated_at'
        ]

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        # Generate unique order number
        last_order = Order.objects.order_by('-id').first()
        if last_order:
            last_number = int(last_order.order_number[3:])
            new_number = f"ORD{str(last_number + 1).zfill(6)}"
        else:
            new_number = "ORD000001"
        validated_data['order_number'] = new_number
        return super().create(validated_data)
