from django.shortcuts import render
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Sum, F, Q
from django.utils import timezone
from .models import Order, OrderItem, Payment, MaterialRequirement
from .serializers import (
    OrderListSerializer, OrderDetailSerializer,
    OrderItemSerializer, PaymentSerializer,
    MaterialRequirementSerializer
)

# Create your views here.

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['order_number', 'customer_name', 'customer_email']
    filterset_fields = ['status', 'priority', 'assigned_to']

    def get_serializer_class(self):
        if self.action == 'list':
            return OrderListSerializer
        return OrderDetailSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        # Filter by date range if provided
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date and end_date:
            queryset = queryset.filter(
                order_date__range=[start_date, end_date]
            )
        return queryset

    @action(detail=True, methods=['post'])
    def assign(self, request, pk=None):
        """Assign order to a user"""
        order = self.get_object()
        user_id = request.data.get('user_id')
        if not user_id:
            return Response(
                {'error': 'user_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        order.assigned_to_id = user_id
        order.save()
        return Response(OrderDetailSerializer(order).data)

    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """Update order status"""
        order = self.get_object()
        new_status = request.data.get('status')
        if not new_status:
            return Response(
                {'error': 'status is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if new_status not in dict(Order.ORDER_STATUS):
            return Response(
                {'error': 'Invalid status'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        order.status = new_status
        if new_status == 'delivered':
            order.actual_delivery = timezone.now()
        order.save()
        return Response(OrderDetailSerializer(order).data)

class OrderItemViewSet(viewsets.ModelViewSet):
    queryset = OrderItem.objects.all()
    serializer_class = OrderItemSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['order', 'product', 'in_production']

    @action(detail=True, methods=['post'])
    def update_production(self, request, pk=None):
        """Update production status and quantity"""
        item = self.get_object()
        produced_qty = request.data.get('produced_quantity')
        if produced_qty is not None:
            item.produced_quantity = produced_qty
        
        production_status = request.data.get('in_production')
        if production_status is not None:
            item.in_production = production_status
            if production_status:
                item.production_started = timezone.now()
            elif item.produced_quantity >= item.quantity:
                item.production_completed = timezone.now()
        
        item.save()
        return Response(OrderItemSerializer(item).data)

class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['reference_number', 'receipt_number']
    filterset_fields = ['order', 'payment_method', 'status']

    def perform_create(self, serializer):
        payment = serializer.save()
        order = payment.order
        
        # Update order's paid amount
        total_paid = order.payments.filter(
            status='completed'
        ).aggregate(
            total=Sum('amount')
        )['total'] or 0
        
        order.paid_amount = total_paid
        order.save()

class MaterialRequirementViewSet(viewsets.ModelViewSet):
    queryset = MaterialRequirement.objects.all()
    serializer_class = MaterialRequirementSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['order_item', 'material']

    @action(detail=True, methods=['post'])
    def allocate(self, request, pk=None):
        """Allocate material to requirement"""
        requirement = self.get_object()
        quantity = request.data.get('quantity')
        if not quantity:
            return Response(
                {'error': 'quantity is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        requirement.allocated_quantity = quantity
        requirement.save()
        return Response(MaterialRequirementSerializer(requirement).data)
