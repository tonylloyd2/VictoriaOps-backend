from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'categories', views.CategoryViewSet)
router.register(r'products', views.ProductViewSet)
router.register(r'specifications', views.ProductSpecificationViewSet)
router.register(r'components', views.ProductComponentViewSet)
router.register(r'documents', views.ProductDocumentViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
