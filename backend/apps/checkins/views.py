import datetime
from rest_framework import generics, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework.views import APIView

from apps.patients.permissions import IsProviderOrAdmin
from .models import DailyCheckIn
from .serializers import DailyCheckInSerializer, DailyCheckInListSerializer
from .scheduler import create_daily_checkins_for_date, send_due_checkins


class CheckInViewSet(ReadOnlyModelViewSet):
    permission_classes = [IsProviderOrAdmin]

    def get_serializer_class(self):
        if self.action == 'list':
            return DailyCheckInListSerializer
        return DailyCheckInSerializer

    def get_queryset(self):
        user = self.request.user
        qs = DailyCheckIn.objects.select_related('patient')

        if user.role == 'provider':
            try:
                qs = qs.filter(patient__assigned_provider=user.provider_profile)
            except Exception:
                qs = qs.none()

        # Filters
        date_str = self.request.query_params.get('date')
        status_filter = self.request.query_params.get('status')
        patient_id = self.request.query_params.get('patient')

        if date_str:
            try:
                d = datetime.date.fromisoformat(date_str)
                qs = qs.filter(scheduled_date=d)
            except ValueError:
                pass
        if status_filter:
            qs = qs.filter(status=status_filter)
        if patient_id:
            qs = qs.filter(patient_id=patient_id)

        return qs

    @action(detail=False, methods=['get'])
    def today(self, request):
        today = datetime.date.today()
        qs = self.get_queryset().filter(scheduled_date=today)
        serializer = DailyCheckInListSerializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def send(self, request, pk=None):
        checkin = self.get_object()
        if checkin.status not in [DailyCheckIn.Status.SCHEDULED, DailyCheckIn.Status.SENT]:
            return Response(
                {'error': f'Cannot send check-in with status {checkin.status}'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        from .scheduler import get_checkin_message
        from apps.messaging.models import Message
        from apps.messaging.services.africastalking_service import AfricasTalkingService
        from django.utils import timezone

        patient = checkin.patient
        body = get_checkin_message(patient)
        result = AfricasTalkingService.send_sms(patient.phone_number_e164, body)

        Message.objects.create(
            patient=patient,
            direction=Message.Direction.OUTBOUND,
            status=Message.Status.SENT if result['status'] == 'sent' else Message.Status.FAILED,
            body=body,
            is_automated=True,
            to_number=patient.phone_number_e164,
            provider_message_id=result.get('message_id') or '',
            checkin=checkin,
            sent_at=timezone.now() if result['status'] == 'sent' else None,
        )

        if result['status'] == 'sent':
            checkin.mark_sent(message_id=result.get('message_id') or '')
            return Response({'status': 'sent'})
        return Response({'status': 'failed', 'error': result.get('error')}, status=status.HTTP_502_BAD_GATEWAY)

    @action(detail=False, methods=['post'])
    def schedule(self, request):
        date_str = request.data.get('date')
        target_date = None
        if date_str:
            try:
                target_date = datetime.date.fromisoformat(date_str)
            except ValueError:
                return Response({'error': 'Invalid date format. Use YYYY-MM-DD'}, status=status.HTTP_400_BAD_REQUEST)
        result = create_daily_checkins_for_date(target_date)
        return Response(result, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'])
    def responses(self, request, pk=None):
        checkin = self.get_object()
        from .serializers import CheckInResponseSerializer
        serializer = CheckInResponseSerializer(checkin.responses.all(), many=True)
        return Response(serializer.data)
