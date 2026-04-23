from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CheckInViewSet

router = DefaultRouter()
router.register('', CheckInViewSet, basename='checkin')

urlpatterns = [
    path('', include(router.urls)),
]
