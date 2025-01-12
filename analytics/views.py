from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiResponse
from datetime import timedelta
from django.db.models import Avg, Count, Sum
from .models import (
    Department, KPI, ProductionMetrics, InventoryMetrics,
    AnalyticsEvent, Report, Alert, DataAggregation
)
from .serializers import (
    DepartmentSerializer, KPISerializer, ProductionMetricsSerializer,
    InventoryMetricsSerializer, AnalyticsEventSerializer, ReportSerializer,
    AlertSerializer, DataAggregationSerializer
)

@extend_schema_view(
    list=extend_schema(
        summary="List departments",
        description="Get a list of all departments"
    ),
    retrieve=extend_schema(
        summary="Get department",
        description="Get details of a specific department"
    )
)
class DepartmentViewSet(viewsets.ModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [IsAuthenticated]

@extend_schema_view(
    list=extend_schema(
        summary="List KPIs",
        description="Get a list of all KPIs"
    ),
    retrieve=extend_schema(
        summary="Get KPI",
        description="Get details of a specific KPI"
    )
)
class KPIViewSet(viewsets.ModelViewSet):
    queryset = KPI.objects.all()
    serializer_class = KPISerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Get KPI trends",
        description="Get trend data for a specific KPI",
        responses={
            200: OpenApiResponse(
                description="KPI trend data",
                response={
                    "type": "object",
                    "properties": {
                        "trend": {"type": "object"},
                        "forecast": {"type": "object"}
                    }
                }
            )
        }
    )
    @action(detail=True)
    def trends(self, request, pk=None):
        kpi = self.get_object()
        return Response({
            'trend': kpi.trend_data,
            'forecast': kpi.forecast_data
        })

@extend_schema_view(
    list=extend_schema(
        summary="List production metrics",
        description="Get a list of all production metrics"
    )
)
class ProductionMetricsViewSet(viewsets.ModelViewSet):
    queryset = ProductionMetrics.objects.all()
    serializer_class = ProductionMetricsSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Get production analysis",
        description="Get analysis of production metrics",
        responses={
            200: OpenApiResponse(
                description="Production metrics analysis",
                response={
                    "type": "object",
                    "properties": {
                        "total_output": {"type": "integer"},
                        "average_efficiency": {"type": "number"},
                        "total_downtime": {"type": "number"}
                    }
                }
            )
        }
    )
    @action(detail=False)
    def analysis(self, request):
        metrics = self.queryset.all()
        return Response({
            'total_output': sum(m.output_quantity for m in metrics),
            'average_efficiency': sum(m.efficiency for m in metrics) / len(metrics) if metrics else 0,
            'total_downtime': sum((m.downtime.total_seconds() for m in metrics), start=0)
        })

@extend_schema_view(
    list=extend_schema(
        summary="List inventory metrics",
        description="Get a list of all inventory metrics"
    )
)
class InventoryMetricsViewSet(viewsets.ModelViewSet):
    queryset = InventoryMetrics.objects.all()
    serializer_class = InventoryMetricsSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Get inventory analysis",
        description="Get analysis of inventory metrics",
        responses={
            200: OpenApiResponse(
                description="Inventory metrics analysis",
                response={
                    "type": "object",
                    "properties": {
                        "total_stock_value": {"type": "number"},
                        "average_turnover": {"type": "number"},
                        "total_stockouts": {"type": "integer"}
                    }
                }
            )
        }
    )
    @action(detail=False)
    def analysis(self, request):
        metrics = self.queryset.all()
        return Response({
            'total_stock_value': sum(m.stock_value for m in metrics),
            'average_turnover': sum(m.turnover_rate for m in metrics) / len(metrics) if metrics else 0,
            'total_stockouts': sum(m.stockout_incidents for m in metrics)
        })

@extend_schema_view(
    list=extend_schema(
        summary="List analytics events",
        description="Get a list of all analytics events"
    )
)
class AnalyticsEventViewSet(viewsets.ModelViewSet):
    queryset = AnalyticsEvent.objects.all()
    serializer_class = AnalyticsEventSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Get event summary",
        description="Get summary of analytics events",
        responses={
            200: OpenApiResponse(
                description="Event summary",
                response={
                    "type": "object",
                    "properties": {
                        "total_events": {"type": "integer"},
                        "by_type": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "event_type": {"type": "string"},
                                    "count": {"type": "integer"}
                                }
                            }
                        }
                    }
                }
            )
        }
    )
    @action(detail=False)
    def summary(self, request):
        events = self.queryset.all()
        return Response({
            'total_events': events.count(),
            'by_type': events.values('event_type').annotate(count=Count('id'))
        })

@extend_schema_view(
    list=extend_schema(
        summary="List reports",
        description="Get a list of all reports"
    )
)
class ReportViewSet(viewsets.ModelViewSet):
    queryset = Report.objects.all()
    serializer_class = ReportSerializer
    permission_classes = [IsAuthenticated]

@extend_schema_view(
    list=extend_schema(
        summary="List alerts",
        description="Get a list of all alerts"
    )
)
class AlertViewSet(viewsets.ModelViewSet):
    queryset = Alert.objects.all()
    serializer_class = AlertSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Get active alerts",
        description="Get a list of currently active alerts",
        responses={
            200: AlertSerializer(many=True)
        }
    )
    @action(detail=False)
    def active(self, request):
        active_alerts = self.queryset.filter(is_active=True)
        serializer = self.get_serializer(active_alerts, many=True)
        return Response(serializer.data)

@extend_schema_view(
    list=extend_schema(
        summary="List data aggregations",
        description="Get a list of all data aggregations"
    )
)
class DataAggregationViewSet(viewsets.ModelViewSet):
    queryset = DataAggregation.objects.all()
    serializer_class = DataAggregationSerializer
    permission_classes = [IsAuthenticated]
