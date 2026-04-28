import hashlib
import hmac
import logging
from django.conf import settings
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.patients.models import Patient
from apps.patients.permissions import IsProviderOrAdmin
from .models import Message, MessageTemplate, FollowUpProgram, PatientProgramEnrollment
from .serializers import (
    MessageSerializer, SendMessageSerializer,
    MessageTemplateSerializer, FollowUpProgramSerializer,
    PatientProgramEnrollmentSerializer,
)
from .services.africastalking_service import AfricasTalkingService
from .inbound_processor import process_inbound_sms

logger = logging.getLogger(__name__)


class MessageListView(generics.ListAPIView):
    serializer_class = MessageSerializer
    permission_classes = [IsProviderOrAdmin]

    def get_queryset(self):
        user = self.request.user
        qs = Message.objects.select_related('patient', 'provider')
        if user.role == 'provider':
            try:
                qs = qs.filter(patient__assigned_provider=user.provider_profile)
            except Exception:
                qs = qs.none()
        return qs


class SendMessageView(APIView):
    permission_classes = [IsProviderOrAdmin]

    def post(self, request):
        serializer = SendMessageSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        patient_id = serializer.validated_data['patient_id']
        body = serializer.validated_data['body']

        # Check patient access
        try:
            patient = Patient.objects.get(pk=patient_id)
        except Patient.DoesNotExist:
            return Response({'error': 'Patient not found'}, status=status.HTTP_404_NOT_FOUND)

        user = request.user
        if user.role == 'provider':
            try:
                if patient.assigned_provider != user.provider_profile:
                    return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)
            except Exception:
                return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)

        if not patient.sms_opt_in:
            return Response({'error': 'Patient has opted out of SMS'}, status=status.HTTP_400_BAD_REQUEST)

        # Create message record
        provider = getattr(user, 'provider_profile', None)
        msg = Message.objects.create(
            patient=patient,
            provider=provider,
            direction=Message.Direction.OUTBOUND,
            status=Message.Status.PENDING,
            body=body,
            is_automated=False,
            to_number=patient.phone_number_e164,
        )

        # Send via Africa's Talking
        result = AfricasTalkingService.send_sms(patient.phone_number_e164, body)

        msg.provider_message_id = result.get('message_id') or ''
        if result['status'] == 'sent':
            msg.status = Message.Status.SENT
            msg.sent_at = timezone.now()
        else:
            msg.status = Message.Status.FAILED
            msg.error_message = result.get('error') or ''
            msg.failed_at = timezone.now()
        msg.save()

        return Response(MessageSerializer(msg).data, status=status.HTTP_201_CREATED)


class MessageTemplateListView(generics.ListCreateAPIView):
    queryset = MessageTemplate.objects.filter(is_active=True)
    serializer_class = MessageTemplateSerializer
    permission_classes = [IsProviderOrAdmin]


class TwilioWebhookView(APIView):
    """Kept for legacy compatibility - redirects to Africa's Talking handler."""
    permission_classes = [AllowAny]

    def post(self, request):
        return Response({'detail': 'Use /webhook/africastalking/ instead.'}, status=status.HTTP_410_GONE)


class AfricasTalkingInboundView(APIView):
    """
    Webhook endpoint for Africa's Talking inbound SMS.
    AT posts: from, to, text, id, date, etc.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        data = request.data
        from_number = data.get('from') or data.get('phoneNumber') or ''
        to_number = data.get('to') or ''
        body = data.get('text') or data.get('body') or ''

        if not from_number or not body:
            return Response({'error': 'Missing required fields'}, status=status.HTTP_400_BAD_REQUEST)

        result = process_inbound_sms(
            from_number=from_number,
            to_number=to_number,
            body=body,
            raw_payload=dict(data),
        )
        return Response(result, status=status.HTTP_200_OK)


class AfricasTalkingDeliveryView(APIView):
    """
    Webhook endpoint for Africa's Talking delivery reports.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        data = request.data
        msg_id = data.get('id') or ''
        delivery_status = data.get('status') or ''

        if msg_id:
            msg = Message.objects.filter(provider_message_id=msg_id).first()
            if msg:
                from .models import DeliveryReceipt
                DeliveryReceipt.objects.create(
                    message=msg,
                    provider_message_id=msg_id,
                    status=delivery_status,
                    raw_payload=dict(data),
                )
                if delivery_status.lower() == 'delivered':
                    msg.status = Message.Status.DELIVERED
                    msg.delivered_at = timezone.now()
                    msg.save(update_fields=['status', 'delivered_at'])
                elif delivery_status.lower() in ('failed', 'rejected'):
                    msg.status = Message.Status.FAILED
                    msg.external_status = delivery_status
                    msg.failed_at = timezone.now()
                    msg.save(update_fields=['status', 'external_status', 'failed_at'])

        return Response({'status': 'ok'})


class SimulatorView(APIView):
    """
    SMS/WhatsApp Simulator endpoint.
    GET  /messages/simulator/?phone=+256...  — list simulated messages for a phone
    POST /messages/simulator/               — simulate sending a check-in request
    """
    permission_classes = [IsProviderOrAdmin]

    def get(self, request):
        from .simulator import get_simulated_messages
        phone = request.query_params.get('phone')
        messages = get_simulated_messages(phone_number=phone, limit=50)
        return Response({'messages': messages, 'count': len(messages)})

    def post(self, request):
        from .simulator import simulate_send, build_sms_preview, build_whatsapp_preview
        patient_id = request.data.get('patient_id')
        channel = request.data.get('channel', 'sms')
        custom_body = request.data.get('body')

        if not patient_id:
            return Response({'error': 'patient_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            patient = Patient.objects.get(pk=patient_id)
        except Patient.DoesNotExist:
            return Response({'error': 'Patient not found'}, status=status.HTTP_404_NOT_FOUND)

        if not custom_body:
            from apps.checkins.scheduler import get_checkin_message
            body = get_checkin_message(patient)
        else:
            body = custom_body

        result = simulate_send(to=patient.phone_number_e164, body=body, channel=channel)

        # Store the message in DB too
        Message.objects.create(
            patient=patient,
            direction=Message.Direction.OUTBOUND,
            status=Message.Status.SENT,
            body=body,
            is_automated=True,
            to_number=patient.phone_number_e164,
            provider_message_id=result.get('message_id', ''),
            sent_at=timezone.now(),
        )

        if channel == 'whatsapp':
            preview = build_whatsapp_preview(patient.get_full_name(), body)
        else:
            preview = build_sms_preview(patient.get_full_name(), body)

        return Response({
            'sent': True,
            'channel': channel,
            'patient': patient.get_full_name(),
            'phone': patient.phone_number_e164,
            'preview': preview,
            'message_id': result.get('message_id'),
        }, status=status.HTTP_201_CREATED)


class FollowUpProgramListView(generics.ListCreateAPIView):
    queryset = FollowUpProgram.objects.filter(is_active=True)
    serializer_class = FollowUpProgramSerializer
    permission_classes = [IsProviderOrAdmin]


class PatientProgramEnrollmentListView(generics.ListAPIView):
    serializer_class = PatientProgramEnrollmentSerializer
    permission_classes = [IsProviderOrAdmin]

    def get_queryset(self):
        return PatientProgramEnrollment.objects.select_related('patient', 'program')
