from django.urls import path
from .views import (
    MessageListView, SendMessageView, MessageTemplateListView,
    AfricasTalkingInboundView, AfricasTalkingDeliveryView,
    FollowUpProgramListView, PatientProgramEnrollmentListView,
    TwilioWebhookView,
)

urlpatterns = [
    path('', MessageListView.as_view(), name='message-list'),
    path('send/', SendMessageView.as_view(), name='message-send'),
    path('templates/', MessageTemplateListView.as_view(), name='message-templates'),
    path('programs/', FollowUpProgramListView.as_view(), name='followup-programs'),
    path('enrollments/', PatientProgramEnrollmentListView.as_view(), name='program-enrollments'),

    # Webhooks
    path('webhook/africastalking/', AfricasTalkingInboundView.as_view(), name='at-inbound'),
    path('webhook/africastalking/delivery/', AfricasTalkingDeliveryView.as_view(), name='at-delivery'),
    path('webhook/twilio/', TwilioWebhookView.as_view(), name='twilio-legacy'),
]
