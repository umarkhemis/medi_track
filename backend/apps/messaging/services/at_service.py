"""
Africa's Talking service for sending SMS messages.
"""

import os
from django.conf import settings


class AfricasTalkingService:
    """Service class for interacting with Africa's Talking API."""

    def __init__(self):
        """Initialize Africa's Talking client with credentials from settings."""
        self.username = getattr(settings, 'AT_USERNAME', os.environ.get('AT_USERNAME', 'sandbox'))
        self.api_key = getattr(settings, 'AT_API_KEY', os.environ.get('AT_API_KEY', ''))
        self.sender_id = getattr(settings, 'AT_SENDER_ID', os.environ.get('AT_SENDER_ID', '')) or None
        self._sms = None

        try:
            import africastalking
            if self.api_key:
                africastalking.initialize(self.username, self.api_key)
                self._sms = africastalking.SMS
            else:
                print(
                    "Warning: Africa's Talking API key not configured. "
                    "Messages will be logged but not sent."
                )
        except ImportError:
            print(
                "Warning: africastalking package not installed. "
                "Messages will be logged but not sent."
            )

    def send_sms(self, to_number, message):
        """
        Send SMS message via Africa's Talking.

        Args:
            to_number (str): Recipient phone number (international E.164 format, e.g. +254XXXXXXXXX)
            message (str): Message content

        Returns:
            dict: Result with success status, message ID, and status
        """
        if not self._sms:
            # Mock mode — log without exposing phone number
            print(f"[AT MOCK] SMS to recipient: {message[:60]}...")
            return {
                'success': True,
                'mock': True,
                'sid': 'MOCK_ID',
                'status': 'mock',
            }

        try:
            if not to_number.startswith('+'):
                to_number = f'+{to_number}'

            kwargs = {
                'message': message,
                'recipients': [to_number],
            }
            if self.sender_id:
                kwargs['senderId'] = self.sender_id

            response = self._sms.send(**kwargs)
            recipients = response.get('SMSMessageData', {}).get('Recipients', [])

            if recipients:
                recipient = recipients[0]
                # Africa's Talking uses status code 101 to indicate successful submission
                status_code = recipient.get('statusCode', 0)
                success = status_code == 101
                return {
                    'success': success,
                    'sid': recipient.get('messageId', ''),
                    'status': recipient.get('status', ''),
                    'cost': recipient.get('cost', ''),
                    'error': None if success else recipient.get('status', 'Unknown error'),
                }

            return {
                'success': False,
                'error': 'No recipients in response',
            }

        except Exception as exc:
            return {
                'success': False,
                'error': str(exc),
            }

    def send_message(self, to_number, message, channel='sms'):
        """
        Send message via specified channel.

        Africa's Talking supports SMS only (no native WhatsApp).
        WhatsApp channel falls back to SMS.

        Args:
            to_number (str): Recipient phone number
            message (str): Message content
            channel (str): 'sms' or 'whatsapp' (whatsapp falls back to SMS)

        Returns:
            dict: Result with success status and details
        """
        return self.send_sms(to_number, message)

    def format_message(self, template_content, patient):
        """
        Format message template with patient data.

        Args:
            template_content (str): Message template with placeholders
            patient: Patient model instance

        Returns:
            str: Formatted message
        """
        patient_user = getattr(patient, 'user', None)
        first_name = getattr(patient_user, 'first_name', '') or getattr(patient, 'first_name', '')
        last_name = getattr(patient_user, 'last_name', '') or getattr(patient, 'last_name', '')
        patient_name = (
            patient_user.get_full_name()
            if patient_user and hasattr(patient_user, 'get_full_name')
            else f'{first_name} {last_name}'.strip()
        )
        condition = (
            patient.get_condition_display()
            if hasattr(patient, 'get_condition_display')
            else getattr(patient, 'condition', '')
        )
        provider_name = (
            patient.assigned_provider.user.get_full_name()
            if getattr(patient, 'assigned_provider', None) and patient.assigned_provider.user
            else 'your care team'
        )

        replacements = {
            '{patient_name}': patient_name,
            '{first_name}': first_name,
            '{last_name}': last_name,
            '{condition}': condition,
            '{discharge_date}': (
                patient.discharge_date.strftime('%B %d, %Y') if patient.discharge_date else 'N/A'
            ),
            '{provider_name}': provider_name,
        }

        message = template_content
        for placeholder, value in replacements.items():
            message = message.replace(placeholder, value)

        return message
