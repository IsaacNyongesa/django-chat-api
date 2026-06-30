from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from apps.common.health import HealthCheckView, ReadinessCheckView

urlpatterns = [
    path('admin/', admin.site.urls),

    # Health / readiness probes for load balancers and orchestrators
    path('healthz/', HealthCheckView.as_view(), name='health'),
    path('readyz/', ReadinessCheckView.as_view(), name='ready'),

    # API
    path('api/auth/', include('apps.users.urls')),
    path('api/', include('apps.chat.urls')),
    path('api/notifications/', include('apps.notifications.urls')),

    # OpenAPI schema + interactive docs
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
