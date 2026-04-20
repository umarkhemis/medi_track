from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.db.models import Case, When, Value, IntegerField
from datetime import timedelta

from .models import Patient
from .serializers import PatientSerializer, PatientListSerializer

# Annotation that orders patients by risk priority: red(2) > yellow(1) > green(0)
RISK_ORDER = Case(
    When(current_risk_level='red', then=Value(2)),
    When(current_risk_level='yellow', then=Value(1)),
    When(current_risk_level='green', then=Value(0)),
    default=Value(0),
    output_field=IntegerField(),
)


class PatientViewSet(viewsets.ModelViewSet):
    """ViewSet for Patient model."""

    queryset = Patient.objects.select_related('user', 'assigned_provider__user').annotate(
        risk_order=RISK_ORDER
    ).order_by('-risk_order', '-created_at')
    serializer_class = PatientSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['condition', 'current_risk_level', 'monitoring_active', 'assigned_provider']
    search_fields = ['user__first_name', 'user__last_name', 'user__email']
    ordering_fields = ['discharge_date', 'current_risk_level', 'created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return PatientListSerializer
        return PatientSerializer

    @action(detail=False, methods=['get'])
    def high_risk(self, request):
        """Get all high-risk patients."""
        patients = self.get_queryset().filter(current_risk_level='red')
        serializer = self.get_serializer(patients, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def pending_response(self, request):
        """Get patients who haven't responded today."""
        from apps.checkins.models import DailyCheckIn

        today = timezone.now().date()
        patients_with_pending = Patient.objects.filter(
            monitoring_active=True,
            checkins__scheduled_date=today,
            checkins__status__in=['scheduled', 'sent']
        ).distinct()

        serializer = self.get_serializer(patients_with_pending, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def checkins(self, request, pk=None):
        """Get patient's check-in history."""
        from apps.checkins.serializers import DailyCheckInSerializer

        patient = self.get_object()
        checkins = patient.checkins.all()[:30]  # Last 30 check-ins
        serializer = DailyCheckInSerializer(checkins, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def alerts(self, request, pk=None):
        """Get patient's alert history."""
        from apps.alerts.serializers import AlertSerializer

        patient = self.get_object()
        alerts = patient.alerts.all()[:50]  # Last 50 alerts
        serializer = AlertSerializer(alerts, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def messages(self, request, pk=None):
        """Get patient's message history."""
        from apps.messaging.serializers import MessageSerializer

        patient = self.get_object()
        messages = patient.messages.all()[:100]  # Last 100 messages
        serializer = MessageSerializer(messages, many=True)
        return Response(serializer.data)

