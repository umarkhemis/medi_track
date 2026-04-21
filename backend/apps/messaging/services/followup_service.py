from datetime import datetime, timedelta

from django.utils import timezone

from apps.messaging.models import FollowUpSchedule, Message
from apps.messaging.services.at_service import AfricasTalkingService
from apps.patients.models import Patient


class FollowUpSchedulerService:
    """Service for automated post-discharge follow-up messaging."""

    def __init__(self):
        self.at_service = AfricasTalkingService()

    def send_due_followups(self, patient_ids=None, schedule_ids=None, force=False):
        now = timezone.now()
        schedules = FollowUpSchedule.objects.filter(is_active=True, template__is_active=True)
        if schedule_ids:
            schedules = schedules.filter(id__in=schedule_ids)

        patients = Patient.objects.filter(
            monitoring_active=True,
            discharge_date__isnull=False,
        ).select_related('user', 'assigned_provider__user')
        if patient_ids:
            patients = patients.filter(id__in=patient_ids)

        stats = {'attempted': 0, 'sent': 0, 'failed': 0, 'skipped': 0}

        for patient in patients:
            discharge_dt = datetime.combine(patient.discharge_date, patient.preferred_check_in_time)
            if timezone.is_naive(discharge_dt):
                discharge_dt = timezone.make_aware(discharge_dt, timezone.get_current_timezone())
            for schedule in schedules:
                trigger_at = discharge_dt + self._to_timedelta(schedule)

                if not force and trigger_at > now:
                    stats['skipped'] += 1
                    continue

                if Message.objects.filter(
                    patient=patient,
                    follow_up_schedule=schedule,
                    direction='outbound',
                    is_automated=True,
                ).exists():
                    stats['skipped'] += 1
                    continue

                stats['attempted'] += 1
                message_content = self.at_service.format_message(schedule.template.content, patient)
                result = self.at_service.send_message(patient.user.phone_number, message_content)

                message = Message.objects.create(
                    patient=patient,
                    provider=patient.assigned_provider,
                    follow_up_schedule=schedule,
                    follow_up_trigger_at=trigger_at,
                    channel='sms',
                    direction='outbound',
                    content=message_content,
                    status='sent' if result.get('success') else 'failed',
                    message_sid=result.get('sid', ''),
                    sent_at=timezone.now() if result.get('success') else None,
                    is_automated=True,
                )

                if result.get('success') or result.get('mock'):
                    stats['sent'] += 1
                    if result.get('mock') and message.status != 'sent':
                        message.status = 'pending'
                        message.save(update_fields=['status'])
                else:
                    stats['failed'] += 1

        return stats

    @staticmethod
    def _to_timedelta(schedule):
        if schedule.interval_unit == 'minutes':
            return timedelta(minutes=schedule.interval_value)
        if schedule.interval_unit == 'hours':
            return timedelta(hours=schedule.interval_value)
        return timedelta(days=schedule.interval_value)
