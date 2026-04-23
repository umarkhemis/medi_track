import logging
import datetime
from django.utils import timezone

logger = logging.getLogger(__name__)


def evaluate_risk(patient, checkin, response_data: dict):
    """
    Evaluate patient risk based on check-in responses.
    Updates patient.current_risk_level and creates Alert/EscalationTask as needed.
    """
    from apps.alerts.models import Alert, EscalationTask

    condition = (patient.condition or '').lower()
    risk_level, alert_title, alert_description, triggered_by = _apply_rules(
        condition, response_data
    )

    # Update patient risk level
    patient.current_risk_level = risk_level
    patient.save(update_fields=['current_risk_level', 'updated_at'])

    if risk_level == 'green':
        logger.info(f'Patient {patient.id} risk: green - no alert')
        return

    # Create alert
    alert = Alert.objects.create(
        patient=patient,
        checkin=checkin,
        severity=risk_level,
        status=Alert.Status.OPEN,
        title=alert_title,
        description=alert_description,
        triggered_by=triggered_by,
        assigned_to=patient.assigned_provider,
    )
    logger.info(f'Alert created: {alert}')

    # Auto-create escalation task for red alerts
    if risk_level == Alert.Severity.RED:
        due = timezone.now() + datetime.timedelta(hours=1)
        task = EscalationTask.objects.create(
            alert=alert,
            patient=patient,
            assigned_to=patient.assigned_provider,
            status=EscalationTask.Status.PENDING,
            instructions=(
                f'URGENT: Patient {patient.get_full_name()} has triggered a RED alert. '
                f'Reason: {alert_title}. Please contact the patient immediately.'
            ),
            due_by=due,
        )
        logger.info(f'EscalationTask created: {task}')


def _apply_rules(condition: str, responses: dict) -> tuple:
    """
    Returns (risk_level, alert_title, alert_description, triggered_by)
    """
    # --- Heart Failure rules ---
    if 'heart failure' in condition:
        if _is_yes(responses, 'chest_pain'):
            return (
                'red',
                'Chest Pain Reported',
                'Patient reported chest pain during daily check-in.',
                'chest_pain=yes',
            )
        if _is_yes(responses, 'shortness_of_breath') and _is_yes(responses, 'leg_swelling'):
            return (
                'yellow',
                'Shortness of Breath + Leg Swelling',
                'Patient reported both shortness of breath and leg swelling.',
                'shortness_of_breath=yes,leg_swelling=yes',
            )

    # --- COPD rules ---
    if 'copd' in condition:
        if _is_yes(responses, 'breathlessness') and _is_yes(responses, 'rescue_inhaler_use'):
            return (
                'red',
                'Increased Breathlessness + Rescue Inhaler Use',
                'Patient reported worsening breathlessness and increased use of rescue inhaler.',
                'breathlessness=yes,rescue_inhaler_use=yes',
            )

    # --- Generic positive symptom ---
    positive_keys = [
        k for k, v in responses.items()
        if str(v).lower() in ('yes', '1', 'true')
        and k not in ('medication_taken',)
    ]
    if positive_keys:
        triggered = ','.join(f'{k}=yes' for k in positive_keys)
        return (
            'yellow',
            'Symptoms Reported',
            f'Patient reported positive symptoms: {", ".join(positive_keys)}.',
            triggered,
        )

    # No symptoms
    return ('green', '', '', '')


def _is_yes(responses: dict, key: str) -> bool:
    val = responses.get(key, '')
    return str(val).lower() in ('yes', '1', 'true')
