import datetime
import logging
import uuid
from django.utils import timezone
from apps.patients.models import Patient
from apps.checkins.models import DailyCheckIn

logger = logging.getLogger(__name__)

DEFAULT_QUESTIONS = ['symptoms', 'pain_level', 'medication_taken']

CONDITION_QUESTIONS = {
    'heart failure': ['chest_pain', 'shortness_of_breath', 'leg_swelling', 'medication_taken'],
    'copd': ['breathlessness', 'rescue_inhaler_use', 'cough', 'medication_taken'],
    'diabetes': ['blood_sugar_high', 'dizziness', 'medication_taken'],
}

DEFAULT_CHECKIN_MESSAGE = (
    "Hello {name}, this is your MediTrack daily check-in. "
    "Please reply with YES if you have any symptoms today, or NO if you feel fine. "
    "Reply STOP to opt out."
)

CONDITION_CHECKIN_MESSAGES = {
    'heart failure': (
        "Hello {name}, your daily heart check-in. "
        "Reply 1 for each YES, 2 for NO: "
        "1) Chest pain? 2) Shortness of breath? 3) Leg swelling? 4) Took medications?"
    ),
    'copd': (
        "Hello {name}, your daily COPD check-in. "
        "Reply 1 for YES, 2 for NO: "
        "1) Breathlessness worse? 2) Used rescue inhaler more? 3) Increased cough? 4) Took medications?"
    ),
}


def get_questions_for_patient(patient: Patient) -> list:
    condition = (patient.condition or '').lower()
    for key in CONDITION_QUESTIONS:
        if key in condition:
            return CONDITION_QUESTIONS[key]
    return DEFAULT_QUESTIONS


def get_checkin_message(patient: Patient) -> str:
    condition = (patient.condition or '').lower()
    for key in CONDITION_CHECKIN_MESSAGES:
        if key in condition:
            return CONDITION_CHECKIN_MESSAGES[key].format(name=patient.first_name)
    return DEFAULT_CHECKIN_MESSAGE.format(name=patient.first_name)


def create_daily_checkins_for_date(target_date: datetime.date = None) -> dict:
    """
    Create one DailyCheckIn per active, opted-in patient for the given date.
    Skips patients who already have a check-in for that date.
    """
    if target_date is None:
        target_date = datetime.date.today()

    active_patients = Patient.objects.filter(
        monitoring_active=True,
        sms_opt_in=True,
        status=Patient.Status.ACTIVE,
    ).select_related('assigned_provider')

    created = 0
    skipped = 0

    for patient in active_patients:
        # Skip if follow-up period ended
        if patient.follow_up_end_date and target_date > patient.follow_up_end_date:
            patient.status = Patient.Status.COMPLETED
            patient.monitoring_active = False
            patient.save(update_fields=['status', 'monitoring_active'])
            skipped += 1
            continue

        # Build scheduled datetime
        preferred_time = patient.preferred_check_in_time or datetime.time(9, 0)
        scheduled_dt = timezone.make_aware(
            datetime.datetime.combine(target_date, preferred_time)
        )

        questions = get_questions_for_patient(patient)

        _, was_created = DailyCheckIn.objects.get_or_create(
            patient=patient,
            scheduled_date=target_date,
            defaults={
                'scheduled_time': scheduled_dt,
                'status': DailyCheckIn.Status.SCHEDULED,
                'question_keys': questions,
                'correlation_id': str(uuid.uuid4()),
            },
        )
        if was_created:
            created += 1
        else:
            skipped += 1

    logger.info(f'create_daily_checkins: date={target_date}, created={created}, skipped={skipped}')
    return {'created': created, 'skipped': skipped, 'date': str(target_date)}


def send_due_checkins() -> dict:
    """
    Send scheduled check-ins whose scheduled_time has arrived.
    """
    from apps.messaging.models import Message
    from apps.messaging.services.africastalking_service import AfricasTalkingService

    now = timezone.now()
    due = DailyCheckIn.objects.filter(
        status=DailyCheckIn.Status.SCHEDULED,
        scheduled_time__lte=now,
        patient__sms_opt_in=True,
        patient__monitoring_active=True,
    ).select_related('patient')

    sent = 0
    failed = 0

    for checkin in due:
        patient = checkin.patient
        message_body = get_checkin_message(patient)

        msg = Message.objects.create(
            patient=patient,
            direction=Message.Direction.OUTBOUND,
            status=Message.Status.PENDING,
            body=message_body,
            is_automated=True,
            to_number=patient.phone_number_e164,
            checkin=checkin,
        )

        result = AfricasTalkingService.send_sms(patient.phone_number_e164, message_body)

        if result['status'] == 'sent':
            msg.status = Message.Status.SENT
            msg.sent_at = now
            msg.provider_message_id = result.get('message_id') or ''
            msg.save()
            checkin.mark_sent(message_id=result.get('message_id') or '')
            sent += 1
        else:
            msg.status = Message.Status.FAILED
            msg.error_message = result.get('error') or ''
            msg.failed_at = now
            msg.save()
            checkin.attempt_count += 1
            checkin.last_attempt_time = now
            checkin.save(update_fields=['attempt_count', 'last_attempt_time'])
            failed += 1

    logger.info(f'send_due_checkins: sent={sent}, failed={failed}')
    return {'sent': sent, 'failed': failed}


def send_checkin_reminders(reminder_delay_hours: int = 4) -> dict:
    """
    Send reminder to patients who haven't replied after reminder_delay_hours.
    """
    import datetime
    from apps.messaging.models import Message
    from apps.messaging.services.africastalking_service import AfricasTalkingService

    now = timezone.now()
    cutoff = now - datetime.timedelta(hours=reminder_delay_hours)

    pending = DailyCheckIn.objects.filter(
        status=DailyCheckIn.Status.SENT,
        sent_time__lte=cutoff,
        reminder_count=0,
        patient__sms_opt_in=True,
        patient__monitoring_active=True,
    ).select_related('patient')

    sent = 0
    for checkin in pending:
        patient = checkin.patient
        reminder_body = (
            f"Hi {patient.first_name}, just a reminder to reply to your daily health check-in. "
            f"Reply YES or NO. Reply STOP to opt out."
        )

        msg = Message.objects.create(
            patient=patient,
            direction=Message.Direction.OUTBOUND,
            status=Message.Status.PENDING,
            body=reminder_body,
            is_automated=True,
            to_number=patient.phone_number_e164,
            checkin=checkin,
        )

        result = AfricasTalkingService.send_sms(patient.phone_number_e164, reminder_body)

        if result['status'] == 'sent':
            msg.status = Message.Status.SENT
            msg.sent_at = now
            msg.provider_message_id = result.get('message_id') or ''
            msg.save()
            checkin.mark_reminded(message_id=result.get('message_id') or '')
            sent += 1
        else:
            msg.status = Message.Status.FAILED
            msg.error_message = result.get('error') or ''
            msg.failed_at = now
            msg.save()

    logger.info(f'send_checkin_reminders: sent={sent}')
    return {'sent': sent}


def mark_missed_checkins() -> dict:
    """
    Mark all expired unanswered check-ins as missed.
    """
    now = timezone.now()
    expired = DailyCheckIn.objects.filter(
        status__in=[DailyCheckIn.Status.SENT, DailyCheckIn.Status.REMINDED],
        expiration_time__lt=now,
    )
    count = expired.count()
    for checkin in expired:
        checkin.mark_missed()

    logger.info(f'mark_missed_checkins: marked={count}')
    return {'marked': count}
