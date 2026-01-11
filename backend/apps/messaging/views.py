from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone

from .models import MessageTemplate, Message
from .serializers import MessageTemplateSerializer, MessageSerializer


class MessageTemplateViewSet(viewsets.ModelViewSet):
    """ViewSet for MessageTemplate model."""
    
    queryset = MessageTemplate.objects.all()
    serializer_class = MessageTemplateSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['template_type', 'condition', 'is_active']
    ordering_fields = ['created_at', 'template_type']


class MessageViewSet(viewsets.ModelViewSet):
    """ViewSet for Message model."""
    
    queryset = Message.objects.select_related('patient__user', 'provider__user').all()
    serializer_class = MessageSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['patient', 'provider', 'channel', 'direction', 'status']
    ordering_fields = ['created_at', 'sent_at']
    
    @action(detail=False, methods=['post'])
    def send(self, request):
        """Send a message to a patient."""
        # TODO: Integrate with TwilioService
        patient_id = request.data.get('patient_id')
        content = request.data.get('content')
        channel = request.data.get('channel', 'sms')
        
        if not patient_id or not content:
            return Response(
                {'error': 'patient_id and content are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create message record
        message = Message.objects.create(
            patient_id=patient_id,
            provider=request.user.provider_profile if hasattr(request.user, 'provider_profile') else None,
            channel=channel,
            direction='outbound',
            content=content,
            status='pending'
        )
        
        serializer = self.get_serializer(message)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class TwilioWebhookView(APIView):
    """Handle incoming SMS/WhatsApp messages from Twilio."""
    
    permission_classes = [AllowAny]
    
    def post(self, request):
        from apps.patients.models import Patient
        
        from_number = request.data.get('From', '').replace('whatsapp:', '')
        body = request.data.get('Body', '').strip()
        message_sid = request.data.get('MessageSid', '')
        
        # Find patient by phone number
        try:
            user = Patient.objects.get(user__phone_number=from_number)
            patient = user.patient_profile
        except Patient.DoesNotExist:
            return Response({'status': 'unknown_sender'})
        
        # Create message record
        Message.objects.create(
            patient=patient,
            channel='whatsapp' if 'whatsapp:' in request.data.get('From', '') else 'sms',
            direction='inbound',
            content=body,
            status='delivered',
            twilio_sid=message_sid,
            delivered_at=timezone.now()
        )
        
        # TODO: Process patient response for check-ins
        
        return Response({'status': 'received'})
