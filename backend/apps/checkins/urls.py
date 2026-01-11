from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DailyCheckInViewSet

router = DefaultRouter()
router.register(r'', DailyCheckInViewSet, basename='checkin')

app_name = 'checkins'

urlpatterns = [
    path('', include(router.urls)),
]
