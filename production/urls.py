from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'lines', views.ProductionLineViewSet)
router.register(r'orders', views.ProductionOrderViewSet)
router.register(r'batches', views.ProductionBatchViewSet)
router.register(r'consumptions', views.MaterialConsumptionViewSet)
router.register(r'quality-checks', views.QualityCheckViewSet)
router.register(r'maintenance', views.MaintenanceLogViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
