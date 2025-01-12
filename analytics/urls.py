from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AnalyticsEventViewSet, ReportViewSet, KPIViewSet,
    AlertViewSet, DataAggregationViewSet
)

router = DefaultRouter()
router.register(r'events', AnalyticsEventViewSet)
router.register(r'reports', ReportViewSet)
router.register(r'kpis', KPIViewSet)
router.register(r'alerts', AlertViewSet)
router.register(r'aggregations', DataAggregationViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
