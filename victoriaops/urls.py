"""
URL configuration for victoriaops project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from core.admin import admin_site
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

admin_site.site_header = 'VictoriaOps Administration'
admin_site.site_title = 'VictoriaOps Admin Portal'
admin_site.index_title = 'Welcome to VictoriaOps Management Portal'

urlpatterns = [
    # Admin URLs
    path('admin/', admin_site.urls),
    
    # Authentication
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(api_version='v1'), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    
    # API URLs
    path('api/auth/', include('rest_framework.urls')),
    path('api/inventory/', include('inventory.urls')),
    path('api/orders/', include('orders.urls')),
    path('api/products/', include('products.urls')),
    path('api/hr/', include('hr_management.urls')),
    path('api/production/', include('production.urls')),
    path('api/analytics/', include('analytics.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
