"""
Check-in scheduler service for creating and sending daily check-ins.
"""

from django.utils import timezone
from django.db.models import Q
from apps.checkins.models import DailyCheckIn
from apps.patients.models import Patient
from apps.messaging.models import MessageTemplate, Message
from apps.messaging.services.at_service import AfricasTalkingService


def _extract_question_keys(questions):
    """
    Extract an ordered list of question keys from a template's questions field.

    Supports two formats:
    - List of dicts: [{"key": "shortness_of_breath", "text": "..."}]
    - List of strings: ["Shortness of breath?", ...]  → generic keys q_1, q_2, …
    """
    if not questions:
        return []
    keys = []
    for idx, q in enumerate(questions):
        if isinstance(q, dict) and 'key' in q:
            keys.append(q['key'])
        else:
            keys.append(f'q_{idx + 1}')
    return keys


def _build_question_lines(questions):
    """Return a numbered list string for the message body."""
    lines = []
    for idx, q in enumerate(questions, 1):
        text = q.get('text', q) if isinstance(q, dict) else q
        lines.append(f"{idx}. {text}")
    return "\n".join(lines)


class CheckInScheduler:
    """Service for scheduling and sending patient check-ins."""

    def __init__(self):
        """Initialize the scheduler with the Africa's Talking service."""
        self.at_service = AfricasTalkingService()

    def create_daily_checkins(self, date=None):
        """
        Create check-in records for all active patients for the specified date.

        Args:
            date: Date to create check-ins for (defaults to today)

        Returns:
            int: Number of check-ins created
        """
        if date is None:
            date = timezone.now().date()

        active_patients = Patient.objects.filter(monitoring_active=True)
        created_count = 0

        for patient in active_patients:
            _, created = DailyCheckIn.objects.get_or_create(
                patient=patient,
                scheduled_date=date,
                defaults={
                    'scheduled_time': patient.preferred_check_in_time,
                    'status': 'scheduled',
                },
            )
            if created:
                created_count += 1

        return created_count

    def send_pending_checkins(self):
        """
        Send check-in messages for scheduled check-ins whose time has arrived.

        Returns:
            dict: Statistics about sent check-ins
        """
        now = timezone.now()

        pending = DailyCheckIn.objects.filter(
            status='scheduled',
            scheduled_date=now.date(),
            scheduled_time__lte=now.time(),
        ).select_related('patient__user', 'patient__assigned_provider__user')

        stats = {'total': pending.count(), 'sent': 0, 'failed': 0}

        for checkin in pending:
            result = self.send_checkin_message(checkin)
            if result['success']:
                stats['sent'] += 1
            else:
                stats['failed'] += 1

        return stats

    def send_checkin_message(self, checkin):
        """
        Send the check-in message to a patient.

        Args:
            checkin: DailyCheckIn instance

        Returns:
            dict: Result with success status and message details
        """
        patient = checkin.patient

        # Find the most specific active template (condition-match beats 'all')
        template = MessageTemplate.objects.filter(
            template_type='daily_checkin',
            is_active=True,
        ).filter(
            Q(condition=patient.condition) | Q(condition='all')
        ).order_by(
            # Prefer exact condition match: non-'all' strings are non-empty so sort DESC
            '-condition',
            '-created_at',
        ).first()

        if not template:
            return {'success': False, 'error': 'No active check-in template found'}

        # Format message body
        message_content = self.at_service.format_message(template.content, patient)

        # Append numbered questions if present
        if template.questions:
            message_content += "\n\n" + _build_question_lines(template.questions)

        # Derive and store question keys so the webhook can map responses correctly
        question_keys = _extract_question_keys(template.questions)
        checkin.question_keys = question_keys
        checkin.save(update_fields=['question_keys'])

        result = self.at_service.send_message(patient.user.phone_number, message_content)

        if result.get('success') or result.get('mock'):
            checkin.status = 'sent'
            checkin.sent_at = timezone.now()
            checkin.save(update_fields=['status', 'sent_at'])

            Message.objects.create(
                patient=patient,
                provider=patient.assigned_provider,
                channel='sms',
                direction='outbound',
                content=message_content,
                status='sent' if result.get('success') else 'pending',
                message_sid=result.get('sid', ''),
                sent_at=timezone.now(),
                is_automated=True,
                related_checkin=checkin,
            )

            return {'success': True, 'checkin_id': checkin.id, 'message_sid': result.get('sid')}

        return {'success': False, 'error': result.get('error', 'Unknown error')}

    def send_reminders(self):
        """
        Send reminder messages to patients who haven't responded to check-ins.

        Returns:
            dict: Statistics about sent reminders
        """
        now = timezone.now()
        reminder_threshold = now - timezone.timedelta(hours=2)

        needs_reminder = DailyCheckIn.objects.filter(
            status='sent',
            sent_at__lte=reminder_threshold,
            scheduled_date=now.date(),
        ).select_related('patient__user')

        stats = {'total': needs_reminder.count(), 'sent': 0, 'failed': 0}

        for checkin in needs_reminder:
            result = self.send_reminder_message(checkin)
            if result['success']:
                stats['sent'] += 1
            else:
                stats['failed'] += 1

        return stats

    def send_reminder_message(self, checkin):
        """
        Send a reminder message for a pending check-in.

        Args:
            checkin: DailyCheckIn instance

        Returns:
            dict: Result with success status
        """
        patient = checkin.patient

        template = MessageTemplate.objects.filter(
            template_type='reminder',
            is_active=True,
        ).first()

        if not template:
            message_content = (
                f"Reminder: {patient.user.get_full_name()}, please complete "
                f"your daily health check-in. Reply to the previous message "
                f"with your responses."
            )
        else:
            message_content = self.at_service.format_message(template.content, patient)

        result = self.at_service.send_message(patient.user.phone_number, message_content)

        if result.get('success') or result.get('mock'):
            Message.objects.create(
                patient=patient,
                provider=patient.assigned_provider,
                channel='sms',
                direction='outbound',
                content=message_content,
                status='sent' if result.get('success') else 'pending',
                message_sid=result.get('sid', ''),
                sent_at=timezone.now(),
                is_automated=True,
                related_checkin=checkin,
            )
            return {'success': True}

        return {'success': False, 'error': result.get('error')}

    def mark_missed_checkins(self):
        """
        Mark check-ins as missed if they weren't completed by end of day.

        Returns:
            int: Number of check-ins marked as missed
        """
        yesterday = timezone.now().date() - timezone.timedelta(days=1)

        count = DailyCheckIn.objects.filter(
            scheduled_date=yesterday,
            status__in=['scheduled', 'sent', 'in_progress'],
        ).update(status='missed')

        return count

