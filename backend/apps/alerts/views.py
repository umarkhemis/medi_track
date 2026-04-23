from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet

from apps.patients.permissions import IsProviderOrAdmin
from .models import Alert, EscalationTask
from .serializers import AlertSerializer, EscalationTaskSerializer


class AlertViewSet(ReadOnlyModelViewSet):
    serializer_class = AlertSerializer
    permission_classes = [IsProviderOrAdmin]

    def get_queryset(self):
        user = self.request.user
        qs = Alert.objects.select_related('patient', 'assigned_to', 'checkin')

        if user.role == 'provider':
            try:
                qs = qs.filter(patient__assigned_provider=user.provider_profile)
            except Exception:
                qs = qs.none()

        severity = self.request.query_params.get('severity')
        alert_status = self.request.query_params.get('status')
        patient_id = self.request.query_params.get('patient')

        if severity:
            qs = qs.filter(severity=severity)
        if alert_status:
            qs = qs.filter(status=alert_status)
        if patient_id:
            qs = qs.filter(patient_id=patient_id)

        return qs

    @action(detail=False, methods=['get'])
    def active(self, request):
        qs = self.get_queryset().filter(status=Alert.Status.OPEN)
        serializer = AlertSerializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def acknowledge(self, request, pk=None):
        alert = self.get_object()
        if alert.status != Alert.Status.OPEN:
            return Response(
                {'error': 'Alert is not open'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        alert.status = Alert.Status.ACKNOWLEDGED
        alert.acknowledged_by = request.user
        alert.acknowledged_at = timezone.now()
        alert.save(update_fields=['status', 'acknowledged_by', 'acknowledged_at', 'updated_at'])
        return Response(AlertSerializer(alert).data)

    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        alert = self.get_object()
        if alert.status == Alert.Status.RESOLVED:
            return Response({'error': 'Alert already resolved'}, status=status.HTTP_400_BAD_REQUEST)
        notes = request.data.get('resolution_notes', '')
        alert.status = Alert.Status.RESOLVED
        alert.resolved_by = request.user
        alert.resolved_at = timezone.now()
        alert.resolution_notes = notes
        alert.save(update_fields=[
            'status', 'resolved_by', 'resolved_at', 'resolution_notes', 'updated_at'
        ])
        return Response(AlertSerializer(alert).data)


class EscalationTaskViewSet(ReadOnlyModelViewSet):
    serializer_class = EscalationTaskSerializer
    permission_classes = [IsProviderOrAdmin]

    def get_queryset(self):
        user = self.request.user
        qs = EscalationTask.objects.select_related('patient', 'assigned_to', 'alert')
        if user.role == 'provider':
            try:
                qs = qs.filter(patient__assigned_provider=user.provider_profile)
            except Exception:
                qs = qs.none()
        return qs

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        task = self.get_object()
        action_taken = request.data.get('action_taken', '')
        task.status = EscalationTask.Status.COMPLETED
        task.action_taken = action_taken
        task.completed_at = timezone.now()
        task.save(update_fields=['status', 'action_taken', 'completed_at'])
        return Response(EscalationTaskSerializer(task).data)
