from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

urlpatterns = [
    path('admin/', admin.site.urls),

    # API docs
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # App routes
    path('api/auth/', include('apps.users.urls')),
    path('api/patients/', include('apps.patients.urls')),
    path('api/providers/', include('apps.providers.urls')),
    path('api/checkins/', include('apps.checkins.urls')),
    path('api/alerts/', include('apps.alerts.urls')),
    path('api/messages/', include('apps.messaging.urls')),
    path('api/analytics/', include('apps.analytics.urls')),
]
