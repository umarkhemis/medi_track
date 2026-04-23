import logging
import uuid
from django.utils import timezone
from apps.messaging.utils.phone import normalize_to_e164

logger = logging.getLogger(__name__)


def process_inbound_sms(from_number: str, to_number: str, body: str, raw_payload: dict) -> dict:
    """
    Main entry point for processing inbound SMS from Africa's Talking webhook.
    Returns a dict with processing result info.
    """
    from apps.messaging.models import InboundWebhookEvent, Message
    from apps.patients.models import Patient
    from apps.checkins.models import DailyCheckIn

    # Build idempotency key
    event_id = raw_payload.get('id') or raw_payload.get('messageId') or str(uuid.uuid4())

    # Store webhook event for idempotency
    if InboundWebhookEvent.objects.filter(event_id=event_id).exists():
        logger.info(f'Duplicate inbound event {event_id}, skipping')
        return {'status': 'duplicate', 'event_id': event_id}

    event = InboundWebhookEvent.objects.create(
        event_id=event_id,
        from_number=from_number,
        to_number=to_number or '',
        body=body,
        raw_payload=raw_payload,
    )

    # Normalize sender number
    e164 = normalize_to_e164(from_number)
    if not e164:
        event.error = f'Could not normalize phone number: {from_number}'
        event.save(update_fields=['error'])
        return {'status': 'error', 'error': event.error}

    # Find patient by E.164 phone number
    try:
        patient = Patient.objects.get(phone_number_e164=e164)
    except Patient.DoesNotExist:
        event.error = f'No patient found with phone {e164}'
        event.save(update_fields=['error'])
        logger.warning(event.error)
        return {'status': 'no_patient', 'error': event.error}

    # Store inbound message
    inbound_msg = Message.objects.create(
        patient=patient,
        direction=Message.Direction.INBOUND,
        status=Message.Status.RECEIVED,
        body=body,
        from_number=e164,
        to_number=to_number or '',
        is_automated=False,
        raw_payload=raw_payload,
        received_at=timezone.now(),
    )

    # Handle STOP opt-out
    if body.strip().upper() == 'STOP':
        patient.opt_out()
        event.processed = True
        event.save(update_fields=['processed'])
        logger.info(f'Patient {patient.id} opted out via STOP')
        return {'status': 'opted_out', 'patient_id': patient.id}

    # Handle START opt-in
    if body.strip().upper() == 'START':
        patient.sms_opt_in = True
        patient.save(update_fields=['sms_opt_in'])
        event.processed = True
        event.save(update_fields=['processed'])
        return {'status': 'opted_in', 'patient_id': patient.id}

    # Find latest open check-in for this patient
    open_checkin = (
        DailyCheckIn.objects.filter(
            patient=patient,
            status__in=[DailyCheckIn.Status.SENT, DailyCheckIn.Status.REMINDED],
        )
        .order_by('-scheduled_date')
        .first()
    )

    if not open_checkin:
        event.error = 'No open check-in found for patient'
        event.save(update_fields=['error', 'processed'])
        event.processed = True
        event.save(update_fields=['processed'])
        return {'status': 'no_checkin', 'patient_id': patient.id}

    # Link inbound message to check-in
    inbound_msg.checkin = open_checkin
    inbound_msg.save(update_fields=['checkin'])

    # Parse reply and store CheckInResponse rows
    from apps.checkins.models import CheckInResponse
    parsed = _parse_reply(body, open_checkin)

    for question_key, response_value in parsed.items():
        CheckInResponse.objects.create(
            checkin=open_checkin,
            patient=patient,
            question_key=question_key,
            response_value=response_value,
            raw_response_text=body,
            source_message=inbound_msg,
            received_at=timezone.now(),
        )

    # Complete the check-in
    open_checkin.status = DailyCheckIn.Status.COMPLETED
    open_checkin.response_data = parsed
    open_checkin.completed_time = timezone.now()
    open_checkin.save(update_fields=['status', 'response_data', 'completed_time'])

    # Evaluate risk and create alerts
    from apps.alerts.risk_engine import evaluate_risk
    evaluate_risk(patient, open_checkin, parsed)

    event.processed = True
    event.save(update_fields=['processed'])

    return {'status': 'completed', 'patient_id': patient.id, 'checkin_id': open_checkin.id}


def _parse_reply(body: str, checkin) -> dict:
    """
    Parse a patient's SMS reply into structured question/answer pairs.
    Supports simple numeric responses (1=yes, 2=no) or keyword matching.
    """
    body_clean = body.strip().lower()
    questions = checkin.question_keys or []
    parsed = {}

    # Simple single-digit response for the first question
    if body_clean in ('1', 'yes', 'y'):
        if questions:
            parsed[questions[0]] = 'yes'
        else:
            parsed['general_response'] = 'yes'
        return parsed

    if body_clean in ('2', 'no', 'n'):
        if questions:
            parsed[questions[0]] = 'no'
        else:
            parsed['general_response'] = 'no'
        return parsed

    # Multi-part response: try splitting by comma or space
    parts = [p.strip() for p in body_clean.replace(',', ' ').split()]
    for i, part in enumerate(parts):
        if i < len(questions):
            parsed[questions[i]] = 'yes' if part in ('1', 'yes', 'y') else 'no'

    if not parsed:
        parsed['raw_response'] = body.strip()

    return parsed
