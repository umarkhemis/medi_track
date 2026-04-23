import datetime
from rest_framework.response import Response
from rest_framework.views import APIView
from apps.patients.permissions import IsProviderOrAdmin
from apps.patients.models import Patient
from apps.checkins.models import DailyCheckIn
from apps.alerts.models import Alert


class SummaryView(APIView):
    permission_classes = [IsProviderOrAdmin]

    def get(self, request):
        user = request.user
        today = datetime.date.today()

        if user.role == 'admin':
            patients = Patient.objects.all()
            checkins = DailyCheckIn.objects.all()
            alerts = Alert.objects.all()
        else:
            try:
                provider = user.provider_profile
            except Exception:
                return Response({'error': 'Provider profile not found'}, status=404)
            patients = Patient.objects.filter(assigned_provider=provider)
            checkins = DailyCheckIn.objects.filter(patient__assigned_provider=provider)
            alerts = Alert.objects.filter(patient__assigned_provider=provider)

        today_checkins = checkins.filter(scheduled_date=today)
        last_7_days = today - datetime.timedelta(days=7)

        return Response({
            'patients': {
                'total': patients.count(),
                'active': patients.filter(monitoring_active=True).count(),
                'opted_out': patients.filter(status=Patient.Status.OPTED_OUT).count(),
                'high_risk': patients.filter(current_risk_level=Patient.RiskLevel.RED).count(),
                'yellow_risk': patients.filter(current_risk_level=Patient.RiskLevel.YELLOW).count(),
                'green_risk': patients.filter(current_risk_level=Patient.RiskLevel.GREEN).count(),
            },
            'checkins_today': {
                'total': today_checkins.count(),
                'completed': today_checkins.filter(status=DailyCheckIn.Status.COMPLETED).count(),
                'missed': today_checkins.filter(status=DailyCheckIn.Status.MISSED).count(),
                'pending': today_checkins.filter(
                    status__in=[DailyCheckIn.Status.SCHEDULED, DailyCheckIn.Status.SENT,
                                DailyCheckIn.Status.REMINDED]
                ).count(),
            },
            'checkins_last_7_days': {
                'total': checkins.filter(scheduled_date__gte=last_7_days).count(),
                'completed': checkins.filter(
                    scheduled_date__gte=last_7_days, status=DailyCheckIn.Status.COMPLETED
                ).count(),
                'missed': checkins.filter(
                    scheduled_date__gte=last_7_days, status=DailyCheckIn.Status.MISSED
                ).count(),
            },
            'alerts': {
                'total_open': alerts.filter(status=Alert.Status.OPEN).count(),
                'red_open': alerts.filter(status=Alert.Status.OPEN, severity=Alert.Severity.RED).count(),
                'yellow_open': alerts.filter(status=Alert.Status.OPEN, severity=Alert.Severity.YELLOW).count(),
                'resolved_last_7_days': alerts.filter(
                    status=Alert.Status.RESOLVED,
                    resolved_at__date__gte=last_7_days,
                ).count(),
            },
        })
