"""
Shared test helpers for MediTrack test suite.
Uses get_or_create for Provider to safely handle the auto-create signal.
"""
from apps.users.models import User
from apps.providers.models import Provider
from apps.patients.models import Patient


def make_provider_user(email='provider@test.com', facility='Test Hospital'):
    user = User.objects.create_user(
        email=email,
        password='TestPass123!',
        first_name='Test',
        last_name='Provider',
        role=User.Role.PROVIDER,
    )
    # Signal may have already created the profile — use get_or_create
    provider, _ = Provider.objects.get_or_create(
        user=user,
        defaults={'facility_name': facility},
    )
    provider.facility_name = facility
    provider.save(update_fields=['facility_name'])
    return user, provider


def make_patient(phone, condition='Heart Failure', provider=None):
    if provider is None:
        _, provider = make_provider_user(email=f'prov_{phone.replace("+", "")}@test.com')
    return Patient.objects.create(
        first_name='Patient',
        last_name='Test',
        phone_number_raw=phone,
        phone_number_e164=phone,
        condition=condition,
        assigned_provider=provider,
        monitoring_active=True,
        sms_opt_in=True,
        status=Patient.Status.ACTIVE,
    )
