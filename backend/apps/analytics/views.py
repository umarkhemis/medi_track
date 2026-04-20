from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Count, Avg


class AnalyticsSummaryView(APIView):
    """System-wide analytics summary for admins / providers."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        from apps.patients.models import Patient
        from apps.alerts.models import Alert
        from apps.checkins.models import DailyCheckIn
        from apps.messaging.models import Message

        today = timezone.now().date()

        # --- Patient risk distribution ---
        patients = Patient.objects.filter(monitoring_active=True)
        total_patients = patients.count()
        risk_distribution = {
            'high': patients.filter(current_risk_level='red').count(),
            'moderate': patients.filter(current_risk_level='yellow').count(),
            'low': patients.filter(current_risk_level='green').count(),
        }

        # --- Condition breakdown ---
        condition_counts = list(
            patients.values('condition').annotate(count=Count('id')).order_by('-count')
        )

        # --- Check-in completion rate (last 7 days) ---
        seven_days_ago = today - timezone.timedelta(days=7)
        week_checkins = DailyCheckIn.objects.filter(scheduled_date__gte=seven_days_ago)
        total_week = week_checkins.count()
        completed_week = week_checkins.filter(status='completed').count()
        missed_week = week_checkins.filter(status='missed').count()
        checkin_rate = round(completed_week / total_week * 100, 1) if total_week > 0 else 0

        # --- Alerts ---
        active_alerts = Alert.objects.filter(status='active').count()
        alerts_today = Alert.objects.filter(created_at__date=today).count()
        alert_type_counts = {
            'red': Alert.objects.filter(status='active', alert_type='red').count(),
            'yellow': Alert.objects.filter(status='active', alert_type='yellow').count(),
        }

        # --- Message stats (last 7 days) ---
        week_messages = Message.objects.filter(created_at__date__gte=seven_days_ago)
        message_stats = {
            'total': week_messages.count(),
            'sent': week_messages.filter(direction='outbound').count(),
            'received': week_messages.filter(direction='inbound').count(),
            'delivered': week_messages.filter(status='delivered').count(),
            'failed': week_messages.filter(status='failed').count(),
        }

        return Response({
            'total_patients': total_patients,
            'risk_distribution': risk_distribution,
            'condition_breakdown': condition_counts,
            'checkin_stats': {
                'period_days': 7,
                'total': total_week,
                'completed': completed_week,
                'missed': missed_week,
                'completion_rate': checkin_rate,
            },
            'alert_stats': {
                'active': active_alerts,
                'today': alerts_today,
                'by_type': alert_type_counts,
            },
            'message_stats': message_stats,
        })

