"""Services for messaging app."""
from .at_service import AfricasTalkingService

# Keep TwilioService name for any legacy code that imports from this package
TwilioService = AfricasTalkingService

__all__ = ['AfricasTalkingService', 'TwilioService']
