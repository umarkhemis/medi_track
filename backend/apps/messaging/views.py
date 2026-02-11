from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone

from .models import MessageTemplate, Message
from .serializers import MessageTemplateSerializer, MessageSerializer
from .services.twilio_service import TwilioService


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
        from apps.patients.models import Patient
        
        patient_id = request.data.get('patient_id')
        content = request.data.get('content')
        channel = request.data.get('channel', 'sms')
        
        if not patient_id or not content:
            return Response(
                {'error': 'patient_id and content are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            patient = Patient.objects.select_related('user').get(id=patient_id)
        except Patient.DoesNotExist:
            return Response(
                {'error': 'Patient not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Send via Twilio
        twilio_service = TwilioService()
        result = twilio_service.send_message(
            patient.user.phone_number,
            content,
            channel=channel
        )
        
        # Create message record
        message = Message.objects.create(
            patient=patient,
            provider=request.user.provider_profile if hasattr(request.user, 'provider_profile') else None,
            channel=channel,
            direction='outbound',
            content=content,
            status='sent' if result.get('success') else 'failed',
            twilio_sid=result.get('sid', ''),
            sent_at=timezone.now() if result.get('success') else None,
            is_automated=False
        )
        
        serializer = self.get_serializer(message)
        response_data = serializer.data
        response_data['twilio_result'] = result
        
        return Response(response_data, status=status.HTTP_201_CREATED)


class TwilioWebhookView(APIView):
    """Handle incoming SMS/WhatsApp messages from Twilio."""
    
    permission_classes = [AllowAny]
    
    def post(self, request):
        from apps.patients.models import Patient
        from apps.checkins.models import DailyCheckIn, CheckInResponse
        from apps.checkins.services.risk_assessment import RiskAssessmentService
        
        from_number = request.data.get('From', '').replace('whatsapp:', '')
        body = request.data.get('Body', '').strip()
        message_sid = request.data.get('MessageSid', '')
        
        # Find patient by phone number
        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            user = User.objects.get(phone_number=from_number)
            patient = user.patient_profile
        except (User.DoesNotExist, AttributeError):
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
        
        # Process patient response for check-ins
        checkin = DailyCheckIn.objects.filter(
            patient=patient,
            scheduled_date=timezone.now().date(),
            status__in=['sent', 'in_progress']
        ).first()
        
        if checkin:
            # Update check-in status
            checkin.status = 'in_progress'
            checkin.save()
            
            # Parse response - expecting numbers separated by spaces
            # Example: "3 5 7" for three questions
            responses = body.split()
            risk_service = RiskAssessmentService()
            
            # Try to create responses for each answer
            for idx, response_text in enumerate(responses):
                question_key = f'question_{idx + 1}'
                parsed_value, score = risk_service.parse_response_value(
                    response_text,
                    question_key
                )
                
                CheckInResponse.objects.create(
                    checkin=checkin,
                    question_key=question_key,
                    question_text=f'Question {idx + 1}',
                    response_value=parsed_value,
                    response_score=score
                )
            
            # If we have enough responses, process the check-in
            if checkin.responses.count() >= 1:
                risk_service.process_checkin(checkin)
        
        return Response({'status': 'received', 'processed': checkin is not None})
