from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from datetime import timedelta, date

from .models import Provider
from .serializers import ProviderSerializer, ProviderDashboardSerializer


class ProviderViewSet(viewsets.ModelViewSet):
    """ViewSet for Provider model."""

    queryset = Provider.objects.select_related('user').all()
    serializer_class = ProviderSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['department', 'is_available']
    search_fields = ['user__first_name', 'user__last_name', 'employee_id']
    ordering_fields = ['created_at', 'employee_id']

    @action(detail=False, methods=['get'])
    def me(self, request):
        """Return the provider profile for the currently authenticated user."""
        try:
            provider = request.user.provider_profile
        except AttributeError:
            return Response(
                {'error': 'Current user does not have a provider profile'},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = self.get_serializer(provider)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def my_dashboard(self, request):
        """Return dashboard summary data for the currently authenticated provider."""
        try:
            provider = request.user.provider_profile
        except AttributeError:
            return Response(
                {'error': 'Current user does not have a provider profile'},
                status=status.HTTP_404_NOT_FOUND,
            )
        return self._build_dashboard_response(provider)

    @action(detail=True, methods=['get'])
    def patients(self, request, pk=None):
        """Get provider's assigned patients."""
        from apps.patients.serializers import PatientListSerializer

        provider = self.get_object()
        patients = provider.patients.all()
        serializer = PatientListSerializer(patients, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def dashboard(self, request, pk=None):
        """Get dashboard summary data for a specific provider."""
        provider = self.get_object()
        return self._build_dashboard_response(provider)

    def _build_dashboard_response(self, provider):
        """Build and return the dashboard data dict for a provider."""
        from apps.patients.models import Patient
        from apps.alerts.models import Alert
        from apps.checkins.models import DailyCheckIn

        today = timezone.now().date()

        patients = provider.patients.filter(monitoring_active=True)
        total_patients = patients.count()
        high_risk = patients.filter(current_risk_level='red').count()
        moderate_risk = patients.filter(current_risk_level='yellow').count()
        low_risk = patients.filter(current_risk_level='green').count()

        active_alerts = Alert.objects.filter(
            patient__assigned_provider=provider,
            status='active',
        ).count()

        today_checkins = DailyCheckIn.objects.filter(
            patient__assigned_provider=provider,
            scheduled_date=today,
        )
        total_today = today_checkins.count()
        completed_today = today_checkins.filter(status='completed').count()
        checkin_response_rate = (completed_today / total_today * 100) if total_today > 0 else 0

        pending_checkins = today_checkins.filter(
            status__in=['scheduled', 'sent', 'in_progress']
        ).count()

        pending_followups = patients.filter(
            follow_up_date__lte=today + timedelta(days=7),
            follow_up_date__gte=today,
        ).count()

        data = {
            'total_patients': total_patients,
            'high_risk_patients': high_risk,
            'moderate_risk_patients': moderate_risk,
            'low_risk_patients': low_risk,
            'active_alerts': active_alerts,
            'pending_checkins': pending_checkins,
            'checkin_response_rate': round(checkin_response_rate, 1),
            'pending_followups': pending_followups,
        }

        serializer = ProviderDashboardSerializer(data=data)
        serializer.is_valid()
        return Response(serializer.data)

    @action(detail=True, methods=['put'])
    def availability(self, request, pk=None):
        """Update provider availability status."""
        provider = self.get_object()
        is_available = request.data.get('is_available')

        if is_available is None:
            return Response(
                {'error': 'is_available field is required'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        provider.is_available = is_available
        provider.save()

        serializer = self.get_serializer(provider)
        return Response(serializer.data)

