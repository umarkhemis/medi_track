"""
Twilio service for sending SMS and WhatsApp messages.
"""

import os
from django.conf import settings
from django.utils import timezone


class TwilioService:
    """Service class for interacting with Twilio API."""
    
    def __init__(self):
        """Initialize Twilio client with credentials from settings."""
        try:
            from twilio.rest import Client
            
            self.account_sid = getattr(settings, 'TWILIO_ACCOUNT_SID', os.environ.get('TWILIO_ACCOUNT_SID'))
            self.auth_token = getattr(settings, 'TWILIO_AUTH_TOKEN', os.environ.get('TWILIO_AUTH_TOKEN'))
            self.sms_from = getattr(settings, 'TWILIO_PHONE_NUMBER', os.environ.get('TWILIO_PHONE_NUMBER'))
            self.whatsapp_from = f"whatsapp:{getattr(settings, 'TWILIO_WHATSAPP_NUMBER', os.environ.get('TWILIO_WHATSAPP_NUMBER'))}"
            
            if self.account_sid and self.auth_token:
                self.client = Client(self.account_sid, self.auth_token)
            else:
                self.client = None
                print("Warning: Twilio credentials not configured. Messages will be logged but not sent.")
        except ImportError:
            self.client = None
            print("Warning: Twilio package not installed. Messages will be logged but not sent.")
    
    def send_sms(self, to_number, message):
        """
        Send SMS message via Twilio.
        
        Args:
            to_number (str): Recipient phone number (E.164 format)
            message (str): Message content
            
        Returns:
            dict: Result with success status, message SID, and status
        """
        if not self.client:
            return {
                'success': False,
                'error': 'Twilio client not configured',
                'mock': True
            }
        
        try:
            # Ensure phone number is in E.164 format
            if not to_number.startswith('+'):
                to_number = f'+{to_number}'
            
            twilio_message = self.client.messages.create(
                body=message,
                from_=self.sms_from,
                to=to_number
            )
            
            return {
                'success': True,
                'sid': twilio_message.sid,
                'status': twilio_message.status,
                'error_code': twilio_message.error_code,
                'error_message': twilio_message.error_message
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def send_whatsapp(self, to_number, message):
        """
        Send WhatsApp message via Twilio.
        
        Args:
            to_number (str): Recipient phone number (E.164 format)
            message (str): Message content
            
        Returns:
            dict: Result with success status, message SID, and status
        """
        if not self.client:
            return {
                'success': False,
                'error': 'Twilio client not configured',
                'mock': True
            }
        
        try:
            # Ensure phone number is in E.164 format
            if not to_number.startswith('+'):
                to_number = f'+{to_number}'
            
            # Add WhatsApp prefix
            if not to_number.startswith('whatsapp:'):
                to_number = f'whatsapp:{to_number}'
            
            twilio_message = self.client.messages.create(
                body=message,
                from_=self.whatsapp_from,
                to=to_number
            )
            
            return {
                'success': True,
                'sid': twilio_message.sid,
                'status': twilio_message.status,
                'error_code': twilio_message.error_code,
                'error_message': twilio_message.error_message
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def send_message(self, to_number, message, channel='sms'):
        """
        Send message via specified channel.
        
        Args:
            to_number (str): Recipient phone number
            message (str): Message content
            channel (str): 'sms' or 'whatsapp'
            
        Returns:
            dict: Result with success status and details
        """
        if channel == 'whatsapp':
            return self.send_whatsapp(to_number, message)
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
        replacements = {
            '{patient_name}': patient.user.get_full_name() or patient.user.username,
            '{first_name}': patient.user.first_name or patient.user.username,
            '{last_name}': patient.user.last_name or '',
            '{condition}': patient.get_condition_display(),
            '{discharge_date}': patient.discharge_date.strftime('%B %d, %Y') if patient.discharge_date else 'N/A',
            '{provider_name}': patient.assigned_provider.user.get_full_name() if patient.assigned_provider else 'your care team',
        }
        
        message = template_content
        for placeholder, value in replacements.items():
            message = message.replace(placeholder, value)
        
        return message
