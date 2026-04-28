from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CheckInViewSet, PatientCheckInSubmitView

router = DefaultRouter()
router.register('', CheckInViewSet, basename='checkin')

urlpatterns = [
    path('submit/', PatientCheckInSubmitView.as_view(), name='checkin-submit'),
    path('', include(router.urls)),
]
