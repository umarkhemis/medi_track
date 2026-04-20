from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone

from .models import MessageTemplate, Message
from .serializers import MessageTemplateSerializer, MessageSerializer
from .services.at_service import AfricasTalkingService


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

    def create(self, request, *args, **kwargs):
        """
        Create a message record and, for outbound messages, actually send via AT.
        Accepts: patient (id), content, channel, direction, is_automated.
        """
        direction = request.data.get('direction', 'outbound')

        if direction == 'outbound':
            from apps.patients.models import Patient

            patient_id = request.data.get('patient')
            content = request.data.get('content', '').strip()
            channel = request.data.get('channel', 'sms')

            if not patient_id or not content:
                return Response(
                    {'error': 'patient and content are required'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            try:
                patient = Patient.objects.select_related('user').get(id=patient_id)
            except Patient.DoesNotExist:
                return Response({'error': 'Patient not found'}, status=status.HTTP_404_NOT_FOUND)

            at_service = AfricasTalkingService()
            result = at_service.send_message(patient.user.phone_number, content, channel=channel)

            message = Message.objects.create(
                patient=patient,
                provider=getattr(request.user, 'provider_profile', None),
                channel=channel,
                direction='outbound',
                content=content,
                status='sent' if result.get('success') else 'failed',
                message_sid=result.get('sid', ''),
                sent_at=timezone.now() if result.get('success') else None,
                is_automated=request.data.get('is_automated', False),
            )

            serializer = self.get_serializer(message)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        # Inbound messages: save as-is (no external sending needed)
        return super().create(request, *args, **kwargs)

    @action(detail=False, methods=['post'])
    def send(self, request):
        """
        Dedicated send endpoint (accepts patient_id instead of patient).
        Kept for backward compatibility with any direct API callers.
        """
        from apps.patients.models import Patient

        patient_id = request.data.get('patient_id')
        content = request.data.get('content', '').strip()
        channel = request.data.get('channel', 'sms')

        if not patient_id or not content:
            return Response(
                {'error': 'patient_id and content are required'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            patient = Patient.objects.select_related('user').get(id=patient_id)
        except Patient.DoesNotExist:
            return Response({'error': 'Patient not found'}, status=status.HTTP_404_NOT_FOUND)

        at_service = AfricasTalkingService()
        result = at_service.send_message(patient.user.phone_number, content, channel=channel)

        message = Message.objects.create(
            patient=patient,
            provider=getattr(request.user, 'provider_profile', None),
            channel=channel,
            direction='outbound',
            content=content,
            status='sent' if result.get('success') else 'failed',
            message_sid=result.get('sid', ''),
            sent_at=timezone.now() if result.get('success') else None,
            is_automated=False,
        )

        serializer = self.get_serializer(message)
        response_data = serializer.data
        response_data['at_result'] = result
        return Response(response_data, status=status.HTTP_201_CREATED)


class AfricasTalkingWebhookView(APIView):
    """
    Handle incoming SMS messages delivered by Africa's Talking.

    AT posts to this endpoint with the following fields:
        from    – sender's phone number (e.g. +254XXXXXXXXX)
        to      – your registered short code / long number
        text    – the message body
        date    – ISO-8601 timestamp
        id      – unique AT message ID
        linkId  – (optional) premium-content link ID
    """

    permission_classes = [AllowAny]

    def post(self, request):
        from apps.patients.models import Patient
        from apps.checkins.models import DailyCheckIn, CheckInResponse
        from apps.checkins.services.risk_assessment import RiskAssessmentService
        from django.contrib.auth import get_user_model

        from_number = request.data.get('from', '').strip()
        body = request.data.get('text', '').strip()
        message_id = request.data.get('id', '')

        if not from_number or not body:
            return Response({'status': 'ignored', 'reason': 'missing fields'})

        # Normalise to E.164 — AT may omit the leading '+'
        if from_number and not from_number.startswith('+'):
            from_number = f'+{from_number}'

        # Find patient by phone number
        User = get_user_model()
        try:
            user = User.objects.get(phone_number=from_number)
            patient = user.patient_profile
        except (User.DoesNotExist, AttributeError):
            return Response({'status': 'unknown_sender'})

        # Record the inbound message
        Message.objects.create(
            patient=patient,
            channel='sms',
            direction='inbound',
            content=body,
            status='delivered',
            message_sid=message_id,
            delivered_at=timezone.now(),
        )

        # Find today's active check-in for this patient
        today = timezone.now().date()
        checkin = DailyCheckIn.objects.filter(
            patient=patient,
            scheduled_date=today,
            status__in=['sent', 'in_progress'],
        ).first()

        if not checkin:
            return Response({'status': 'received', 'processed': False})

        checkin.status = 'in_progress'
        checkin.save()

        # Parse space-separated numeric/word responses, e.g. "4 6 3"
        tokens = body.split()
        risk_service = RiskAssessmentService()

        # Use stored question_keys when available; fall back to generic keys
        question_keys = checkin.question_keys or []

        for idx, token in enumerate(tokens):
            if idx < len(question_keys):
                key = question_keys[idx]
            else:
                key = f'question_{idx + 1}'

            # Derive human-readable text from the key
            question_text = key.replace('_', ' ').title()

            parsed_value, score = risk_service.parse_response_value(token, key)

            # Update existing response for this key if it already exists
            CheckInResponse.objects.update_or_create(
                checkin=checkin,
                question_key=key,
                defaults={
                    'question_text': question_text,
                    'response_value': parsed_value,
                    'response_score': score,
                },
            )

        # Determine how many responses are expected
        expected_count = len(question_keys) if question_keys else len(tokens)
        received_count = checkin.responses.count()

        # Process check-in once all expected responses are in
        if received_count >= expected_count and expected_count > 0:
            risk_service.process_checkin(checkin)

        return Response({'status': 'received', 'processed': True})

