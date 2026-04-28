"""
Twilio SMS/WhatsApp Adapter for MediTrack.

Automatically switches between simulation and real Twilio based on
whether TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN are set in .env.

Usage:
    from apps.messaging.twilio_adapter import TwilioAdapter

    result = TwilioAdapter.send_sms('+256700000000', 'Hello from MediTrack!')
    result = TwilioAdapter.send_whatsapp('+256700000000', 'Your check-in is due.')

To enable real Twilio, add to .env:
    TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    TWILIO_AUTH_TOKEN=your_auth_token
    TWILIO_PHONE_NUMBER=+1234567890
    TWILIO_WHATSAPP_NUMBER=+14155238886  # Twilio WhatsApp sandbox number
"""
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


def _is_twilio_configured() -> bool:
    """Return True if real Twilio credentials are present and non-empty."""
    sid = getattr(settings, 'TWILIO_ACCOUNT_SID', '') or ''
    token = getattr(settings, 'TWILIO_AUTH_TOKEN', '') or ''
    return bool(sid and token and not sid.startswith('your_'))


class TwilioAdapter:
    """
    Unified SMS/WhatsApp adapter.
    - Uses real Twilio when credentials are present in settings.
    - Falls back to the simulator when credentials are absent.
    """

    @classmethod
    def send_sms(cls, to: str, body: str) -> dict:
        """
        Send an SMS message.
        Returns dict: { status, message_id, error, simulated }
        """
        if _is_twilio_configured():
            return cls._send_via_twilio(to, body, channel='sms')
        else:
            return cls._send_simulated(to, body, channel='sms')

    @classmethod
    def send_whatsapp(cls, to: str, body: str) -> dict:
        """
        Send a WhatsApp message.
        Returns dict: { status, message_id, error, simulated }
        """
        if _is_twilio_configured():
            return cls._send_via_twilio(to, body, channel='whatsapp')
        else:
            return cls._send_simulated(to, body, channel='whatsapp')

    @classmethod
    def _send_simulated(cls, to: str, body: str, channel: str = 'sms') -> dict:
        """Send via simulator (no real SMS)."""
        from apps.messaging.simulator import simulate_send
        result = simulate_send(to=to, body=body, channel=channel)
        logger.info(f'[TWILIO ADAPTER] Simulated {channel} to {to}')
        return result

    @classmethod
    def _send_via_twilio(cls, to: str, body: str, channel: str = 'sms') -> dict:
        """Send via real Twilio API."""
        try:
            from twilio.rest import Client
        except ImportError:
            logger.error('twilio package not installed. Run: pip install twilio')
            return {'status': 'failed', 'message_id': None, 'error': 'twilio not installed', 'simulated': False}

        account_sid = getattr(settings, 'TWILIO_ACCOUNT_SID', '')
        auth_token = getattr(settings, 'TWILIO_AUTH_TOKEN', '')

        try:
            client = Client(account_sid, auth_token)

            if channel == 'whatsapp':
                from_number = getattr(settings, 'TWILIO_WHATSAPP_NUMBER', '')
                if not from_number.startswith('whatsapp:'):
                    from_number = f'whatsapp:{from_number}'
                to_number = f'whatsapp:{to}' if not to.startswith('whatsapp:') else to
            else:
                from_number = getattr(settings, 'TWILIO_PHONE_NUMBER', '')
                to_number = to

            message = client.messages.create(
                body=body,
                from_=from_number,
                to=to_number,
            )

            logger.info(f'Twilio {channel} sent: SID={message.sid}')
            return {
                'status': 'sent',
                'message_id': message.sid,
                'error': None,
                'simulated': False,
            }

        except Exception as e:
            logger.exception(f'Twilio send error: {e}')
            return {
                'status': 'failed',
                'message_id': None,
                'error': str(e),
                'simulated': False,
            }

    @classmethod
    def is_using_real_twilio(cls) -> bool:
        """Return True if real Twilio credentials are active."""
        return _is_twilio_configured()
