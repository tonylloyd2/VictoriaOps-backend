from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'orders', views.OrderViewSet)
router.register(r'order-items', views.OrderItemViewSet)
router.register(r'payments', views.PaymentViewSet)
router.register(r'material-requirements', views.MaterialRequirementViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
