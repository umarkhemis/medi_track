"""
SMS/WhatsApp Simulator for MediTrack.

Simulates sending SMS and WhatsApp messages without real Twilio/AT credentials.
When real credentials are present, this module is bypassed automatically.

This is a developer/demo tool for:
- Testing the full check-in flow locally
- Demoing the system without real SMS infrastructure
- Recording sent messages for the SMS simulator UI
"""
import logging
import uuid
import datetime
from django.utils import timezone

logger = logging.getLogger(__name__)


class SimulatedMessage:
    """Represents a simulated SMS/WhatsApp message."""

    def __init__(self, to: str, body: str, from_number: str = 'MediTrack',
                 channel: str = 'sms', message_id: str = None):
        self.message_id = message_id or f'SIM_{uuid.uuid4().hex[:12].upper()}'
        self.to = to
        self.from_number = from_number
        self.body = body
        self.channel = channel
        self.sent_at = timezone.now()
        self.status = 'delivered'

    def to_dict(self) -> dict:
        return {
            'message_id': self.message_id,
            'to': self.to,
            'from': self.from_number,
            'body': self.body,
            'channel': self.channel,
            'sent_at': self.sent_at.isoformat(),
            'status': self.status,
        }


# In-memory store of simulated messages (cleared on restart)
_simulated_messages: list = []


def simulate_send(to: str, body: str, channel: str = 'sms',
                  from_number: str = 'MediTrack') -> dict:
    """
    Simulate sending a message and store it in memory.
    Returns a result dict compatible with AfricasTalkingService.send_sms().
    """
    msg = SimulatedMessage(to=to, body=body, channel=channel, from_number=from_number)
    _simulated_messages.append(msg)
    logger.info(f'[SIMULATOR] {channel.upper()} to {to}: {body[:80]}')

    return {
        'status': 'sent',
        'message_id': msg.message_id,
        'mock': True,
        'simulated': True,
        'error': None,
    }


def get_simulated_messages(phone_number: str = None, limit: int = 50) -> list:
    """
    Retrieve simulated messages, optionally filtered by phone number.
    Returns messages in newest-first order.
    """
    msgs = list(reversed(_simulated_messages))
    if phone_number:
        msgs = [m for m in msgs if m.to == phone_number or m.from_number == phone_number]
    return [m.to_dict() for m in msgs[:limit]]


def clear_simulated_messages():
    """Clear the in-memory message store (for testing)."""
    _simulated_messages.clear()


def build_sms_preview(patient_name: str, body: str, sent_at: datetime.datetime = None) -> dict:
    """
    Build a realistic SMS preview object for the frontend simulator UI.
    """
    if sent_at is None:
        sent_at = timezone.now()

    return {
        'type': 'sms',
        'from': 'MediTrack',
        'to': patient_name,
        'body': body,
        'sent_at': sent_at.isoformat(),
        'status': 'delivered',
        'read': False,
    }


def build_whatsapp_preview(patient_name: str, body: str, sent_at: datetime.datetime = None) -> dict:
    """
    Build a realistic WhatsApp-style preview object for the frontend simulator UI.
    """
    if sent_at is None:
        sent_at = timezone.now()

    return {
        'type': 'whatsapp',
        'from': 'MediTrack',
        'to': patient_name,
        'body': body,
        'sent_at': sent_at.isoformat(),
        'status': 'read',
        'ticks': 2,  # Two blue ticks = read
    }
