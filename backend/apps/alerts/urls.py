from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AlertViewSet, EscalationTaskViewSet

router = DefaultRouter()
router.register('escalations', EscalationTaskViewSet, basename='escalation')
router.register('', AlertViewSet, basename='alert')

urlpatterns = [
    path('', include(router.urls)),
]
