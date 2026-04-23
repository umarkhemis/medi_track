import datetime
from rest_framework import generics, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from .models import Provider
from .serializers import ProviderSerializer, ProviderDashboardSerializer
from apps.patients.models import Patient
from apps.alerts.models import Alert
from apps.checkins.models import DailyCheckIn


class ProviderViewSet(ReadOnlyModelViewSet):
    serializer_class = ProviderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'admin':
            return Provider.objects.select_related('user').all()
        # Providers can only see themselves
        return Provider.objects.filter(user=user).select_related('user')

    @action(detail=True, methods=['get'])
    def dashboard(self, request, pk=None):
        provider = self.get_object()
        today = datetime.date.today()

        patients = Patient.objects.filter(assigned_provider=provider)
        checkins_today = DailyCheckIn.objects.filter(
            patient__assigned_provider=provider, scheduled_date=today
        )

        data = {
            'total_patients': patients.count(),
            'active_patients': patients.filter(monitoring_active=True).count(),
            'high_risk_patients': patients.filter(current_risk_level=Patient.RiskLevel.RED).count(),
            'yellow_risk_patients': patients.filter(current_risk_level=Patient.RiskLevel.YELLOW).count(),
            'pending_alerts': Alert.objects.filter(
                patient__assigned_provider=provider,
                status=Alert.Status.OPEN
            ).count(),
            'todays_checkins': checkins_today.count(),
            'completed_checkins_today': checkins_today.filter(status=DailyCheckIn.Status.COMPLETED).count(),
            'missed_checkins_today': checkins_today.filter(status=DailyCheckIn.Status.MISSED).count(),
        }
        serializer = ProviderDashboardSerializer(data)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def patients(self, request, pk=None):
        provider = self.get_object()
        from apps.patients.serializers import PatientListSerializer
        qs = Patient.objects.filter(assigned_provider=provider)
        serializer = PatientListSerializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['patch'])
    def availability(self, request, pk=None):
        provider = self.get_object()
        is_available = request.data.get('is_available')
        if is_available is None:
            return Response({'error': 'is_available required'}, status=status.HTTP_400_BAD_REQUEST)
        provider.is_available = bool(is_available)
        provider.save(update_fields=['is_available'])
        return Response({'is_available': provider.is_available})
