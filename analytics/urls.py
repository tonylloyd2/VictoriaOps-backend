from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    DepartmentViewSet, KPIViewSet, ProductionMetricsViewSet,
    InventoryMetricsViewSet, AnalyticsEventViewSet, ReportViewSet,
    AlertViewSet, DataAggregationViewSet
)

router = DefaultRouter()
router.register(r'departments', DepartmentViewSet)
router.register(r'kpis', KPIViewSet)
router.register(r'production-metrics', ProductionMetricsViewSet)
router.register(r'inventory-metrics', InventoryMetricsViewSet)
router.register(r'events', AnalyticsEventViewSet)
router.register(r'reports', ReportViewSet)
router.register(r'alerts', AlertViewSet)
router.register(r'data-aggregations', DataAggregationViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
