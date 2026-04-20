"""
Compatibility shim — Twilio has been replaced by Africa's Talking.
Import AfricasTalkingService via the canonical module; keep the
TwilioService name so any stale imports continue to work.
"""
from apps.messaging.services.at_service import AfricasTalkingService

TwilioService = AfricasTalkingService

__all__ = ['TwilioService']
