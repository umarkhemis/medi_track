import datetime
from rest_framework import generics, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny

from apps.patients.permissions import IsProviderOrAdmin
from .models import DailyCheckIn
from .serializers import DailyCheckInSerializer, DailyCheckInListSerializer
from .scheduler import create_daily_checkins_for_date, send_due_checkins

# Standardized symptom questions for the patient check-in form
CHECKIN_QUESTIONS = [
    {
        'key': 'feeling_today',
        'question': 'How are you feeling today overall?',
        'type': 'choice',
        'choices': ['Good', 'Fair', 'Poor', 'Very Poor'],
        'weight': {'Good': 0, 'Fair': 1, 'Poor': 2, 'Very Poor': 3},
    },
    {
        'key': 'pain_level',
        'question': 'Rate your pain level (0 = no pain, 10 = severe)',
        'type': 'scale',
        'min': 0,
        'max': 10,
    },
    {
        'key': 'medication_taken',
        'question': 'Have you taken all your prescribed medications today?',
        'type': 'choice',
        'choices': ['Yes', 'No', 'Partially'],
        'weight': {'Yes': 0, 'Partially': 1, 'No': 2},
    },
    {
        'key': 'new_symptoms',
        'question': 'Are you experiencing any new or worsening symptoms?',
        'type': 'choice',
        'choices': ['No', 'Mild symptoms', 'Moderate symptoms', 'Severe symptoms'],
        'weight': {'No': 0, 'Mild symptoms': 1, 'Moderate symptoms': 2, 'Severe symptoms': 3},
    },
    {
        'key': 'needs_help',
        'question': 'Do you need medical attention or feel you should contact your doctor?',
        'type': 'choice',
        'choices': ['No', 'Maybe', 'Yes'],
        'weight': {'No': 0, 'Maybe': 1, 'Yes': 3},
    },
]


def calculate_risk_level(responses: dict) -> str:
    """
    Calculate risk level from check-in responses.
    Returns 'green', 'yellow', or 'red'.
    """
    score = 0

    feeling = responses.get('feeling_today', 'Good')
    feeling_weights = {'Good': 0, 'Fair': 1, 'Poor': 2, 'Very Poor': 3}
    score += feeling_weights.get(feeling, 0)

    try:
        pain = int(responses.get('pain_level', 0))
        if pain >= 7:
            score += 3
        elif pain >= 4:
            score += 2
        elif pain >= 2:
            score += 1
    except (ValueError, TypeError):
        pass

    med_weights = {'Yes': 0, 'Partially': 1, 'No': 2}
    score += med_weights.get(responses.get('medication_taken', 'Yes'), 0)

    symptom_weights = {'No': 0, 'Mild symptoms': 1, 'Moderate symptoms': 2, 'Severe symptoms': 3}
    score += symptom_weights.get(responses.get('new_symptoms', 'No'), 0)

    help_weights = {'No': 0, 'Maybe': 1, 'Yes': 3}
    score += help_weights.get(responses.get('needs_help', 'No'), 0)

    if score >= 7 or responses.get('needs_help') == 'Yes' or responses.get('feeling_today') == 'Very Poor':
        return 'red'
    elif score >= 3:
        return 'yellow'
    return 'green'


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

    @action(detail=False, methods=['get'])
    def questions(self, request):
        """Return the standardized check-in questions."""
        return Response(CHECKIN_QUESTIONS)

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


class PatientCheckInSubmitView(APIView):
    """
    Public endpoint for patients to submit their daily check-in responses.
    Accessible without authentication (patient uses their phone number as identifier).
    """
    permission_classes = [AllowAny]

    def get(self, request):
        """Return the check-in form questions."""
        return Response({
            'questions': CHECKIN_QUESTIONS,
            'instructions': 'Please answer each question honestly to help your doctor monitor your recovery.',
        })

    def post(self, request):
        from apps.patients.models import Patient
        from apps.alerts.models import Alert
        from apps.messaging.models import Message
        from django.utils import timezone

        phone = request.data.get('phone_number', '').strip()
        responses = request.data.get('responses', {})
        checkin_id = request.data.get('checkin_id')

        if not phone and not checkin_id:
            return Response(
                {'error': 'Provide phone_number or checkin_id'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Find patient
        patient = None
        if phone:
            from apps.messaging.utils.phone import normalize_to_e164
            e164 = normalize_to_e164(phone)
            if e164:
                patient = Patient.objects.filter(phone_number_e164=e164).first()
            if not patient:
                patient = Patient.objects.filter(phone_number_raw=phone).first()
        
        checkin = None
        if checkin_id:
            checkin = DailyCheckIn.objects.filter(pk=checkin_id).first()
            if checkin and not patient:
                patient = checkin.patient

        if not patient:
            return Response({'error': 'Patient not found'}, status=status.HTTP_404_NOT_FOUND)

        if not responses:
            return Response({'error': 'responses are required'}, status=status.HTTP_400_BAD_REQUEST)

        # Get or create today's check-in
        today = datetime.date.today()
        if not checkin:
            checkin, _ = DailyCheckIn.objects.get_or_create(
                patient=patient,
                scheduled_date=today,
                defaults={
                    'status': DailyCheckIn.Status.SENT,
                    'question_keys': list(responses.keys()),
                },
            )

        if checkin.status == DailyCheckIn.Status.COMPLETED:
            return Response(
                {'message': 'Check-in already completed for today', 'status': 'already_completed'},
                status=status.HTTP_200_OK,
            )

        # Save responses and calculate risk
        checkin.response_data = responses
        checkin.status = DailyCheckIn.Status.COMPLETED
        checkin.completed_time = timezone.now()
        checkin.save()

        # Calculate risk level
        risk_level = calculate_risk_level(responses)
        patient.current_risk_level = risk_level
        patient.save(update_fields=['current_risk_level', 'updated_at'])

        # Create individual response records
        from .models import CheckInResponse
        for key, value in responses.items():
            CheckInResponse.objects.get_or_create(
                checkin=checkin,
                patient=patient,
                question_key=key,
                defaults={'response_value': str(value)},
            )

        # Create alert if yellow or red
        if risk_level in ('yellow', 'red'):
            alert_title = (
                f'{"URGENT: " if risk_level == "red" else ""}Patient needs attention'
            )
            description_parts = []
            if responses.get('feeling_today') in ('Poor', 'Very Poor'):
                description_parts.append(f'Feeling: {responses["feeling_today"]}')
            if responses.get('new_symptoms') not in ('No', None):
                description_parts.append(f'Symptoms: {responses["new_symptoms"]}')
            if responses.get('needs_help') in ('Maybe', 'Yes'):
                description_parts.append(f'Needs help: {responses["needs_help"]}')

            Alert.objects.create(
                patient=patient,
                checkin=checkin,
                severity=risk_level,
                status=Alert.Status.OPEN,
                title=alert_title,
                description='; '.join(description_parts) or 'Check-in responses indicate concern',
                triggered_by='check_in_response',
                assigned_to=patient.assigned_provider,
            )

        # Log the check-in as a received message
        Message.objects.create(
            patient=patient,
            direction=Message.Direction.INBOUND,
            status=Message.Status.RECEIVED,
            body=f'Check-in submitted. Risk: {risk_level}. Responses: {responses}',
            is_automated=True,
            from_number=patient.phone_number_e164,
            checkin=checkin,
            received_at=timezone.now(),
        )

        return Response({
            'message': 'Check-in received successfully!',
            'status': 'completed',
            'risk_level': risk_level,
            'checkin_id': checkin.id,
        }, status=status.HTTP_200_OK)
