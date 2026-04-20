"""
Compatibility shim — Twilio has been replaced by Africa's Talking.
Import AfricasTalkingService via the canonical path, but keep the
TwilioService name so any stale imports continue to work during migration.
"""
from apps.messaging.services.at_service import AfricasTalkingService as TwilioService  # noqa: F401

__all__ = ['TwilioService']
