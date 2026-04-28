import logging
from django.conf import settings
from apps.messaging.utils.phone import normalize_to_e164

logger = logging.getLogger(__name__)


class AfricasTalkingService:
    _initialized = False
    _mock_mode = False

    @classmethod
    def _init(cls):
        if not cls._initialized:
            try:
                import africastalking
                api_key = getattr(settings, 'AT_API_KEY', '')
                if api_key:
                    africastalking.initialize(
                        username=settings.AT_USERNAME,
                        api_key=api_key,
                    )
                    cls._initialized = True
                    cls._mock_mode = False
                else:
                    logger.info("AT_API_KEY not configured. Using mock SMS mode.")
                    cls._mock_mode = True
                    cls._initialized = True
            except ImportError:
                logger.info("africastalking package not installed. Using mock SMS mode.")
                cls._mock_mode = True
                cls._initialized = True

    @classmethod
    def get_sms(cls):
        cls._init()
        if cls._mock_mode:
            return None
        import africastalking
        return africastalking.SMS

    @classmethod
    def send_sms(cls, to: str, message: str, sender_id: str = None) -> dict:
        """
        Send an SMS via Africa's Talking.
        `to` should be a raw or E.164 phone number.
        Returns dict with keys: status, message_id, error
        """
        cls._init()

        e164 = normalize_to_e164(to)
        if not e164:
            logger.error(f'AfricasTalking: invalid phone number {to}')
            return {'status': 'failed', 'message_id': None, 'error': 'Invalid phone number'}

        if cls._mock_mode:
            logger.info(f'[AT MOCK] SMS to {e164[:6]}****: {message[:60]}...')
            return {'status': 'sent', 'message_id': 'MOCK_' + e164[-4:], 'error': None}

        sms_sender = sender_id or getattr(settings, 'AT_SMS_SENDER_ID', None)

        try:
            sms = cls.get_sms()
            kwargs = {'message': message, 'recipients': [e164]}
            if sms_sender:
                kwargs['sender_id'] = sms_sender

            response = sms.send(**kwargs)
            logger.info(f'AfricasTalking response: {response}')

            recipients = response.get('SMSMessageData', {}).get('Recipients', [])
            if recipients:
                recipient = recipients[0]
                msg_id = recipient.get('messageId', '')
                status_code = recipient.get('statusCode', 0)
                if status_code == 101:
                    return {'status': 'sent', 'message_id': msg_id, 'error': None}
                else:
                    err = recipient.get('status', 'Unknown error')
                    return {'status': 'failed', 'message_id': msg_id, 'error': err}

            return {'status': 'failed', 'message_id': None, 'error': 'No recipients in response'}

        except Exception as e:
            logger.exception(f'AfricasTalking send_sms error: {e}')
            return {'status': 'failed', 'message_id': None, 'error': str(e)}
