from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MessageTemplateViewSet, MessageViewSet, AfricasTalkingWebhookView

router = DefaultRouter()
router.register(r'templates', MessageTemplateViewSet, basename='template')
router.register(r'', MessageViewSet, basename='message')

app_name = 'messaging'

urlpatterns = [
    path('webhook/africas-talking/', AfricasTalkingWebhookView.as_view(), name='at-webhook'),
    path('', include(router.urls)),
]
