import phonenumbers
from django.conf import settings


def normalize_to_e164(phone_raw: str, country_code: str = None) -> str | None:
    """
    Normalize a phone number string to E.164 format.
    Returns None if the number is invalid.
    """
    if not phone_raw:
        return None

    country = country_code or getattr(settings, 'DEFAULT_COUNTRY_CODE', 'KE')

    try:
        parsed = phonenumbers.parse(phone_raw, country)
        if phonenumbers.is_valid_number(parsed):
            return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
    except phonenumbers.NumberParseException:
        pass

    return None


def is_valid_phone(phone_raw: str, country_code: str = None) -> bool:
    return normalize_to_e164(phone_raw, country_code) is not None
