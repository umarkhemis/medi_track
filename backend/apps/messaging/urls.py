from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MessageTemplateViewSet, MessageViewSet, TwilioWebhookView

router = DefaultRouter()
router.register(r'templates', MessageTemplateViewSet, basename='template')
router.register(r'', MessageViewSet, basename='message')

app_name = 'messaging'

urlpatterns = [
    path('webhook/twilio/', TwilioWebhookView.as_view(), name='twilio-webhook'),
    path('', include(router.urls)),
]
