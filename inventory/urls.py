from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'suppliers', views.SupplierViewSet)
router.register(r'warehouses', views.WarehouseViewSet)
router.register(r'locations', views.StorageLocationViewSet)
router.register(r'materials', views.RawMaterialViewSet)
router.register(r'stock', views.StockViewSet)
router.register(r'movements', views.StockMovementViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
