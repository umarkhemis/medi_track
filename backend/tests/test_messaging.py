import datetime
from django.test import TestCase
from rest_framework.test import APIClient
from apps.checkins.models import DailyCheckIn
from .helpers import make_provider_user, make_patient


class InboundSMSTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_stop_disables_monitoring(self):
        _, prov = make_provider_user(email='p1msg@test.com')
        patient = make_patient('+254700000201', provider=prov)
        response = self.client.post('/api/messages/webhook/africastalking/', {
            'from': '+254700000201', 'to': '+254000000000',
            'text': 'STOP', 'id': 'evt_stop_001',
        }, format='json')
        self.assertEqual(response.status_code, 200)
        patient.refresh_from_db()
        self.assertFalse(patient.sms_opt_in)

    def test_sms_reply_completes_checkin(self):
        from django.utils import timezone
        _, prov = make_provider_user(email='p2msg@test.com')
        patient = make_patient('+254700000202', provider=prov)
        checkin = DailyCheckIn.objects.create(
            patient=patient,
            scheduled_date=datetime.date.today(),
            status=DailyCheckIn.Status.SENT,
            question_keys=['chest_pain'],
        )
        response = self.client.post('/api/messages/webhook/africastalking/', {
            'from': '+254700000202', 'to': '+254000000000',
            'text': 'NO', 'id': 'evt_reply_001',
        }, format='json')
        self.assertEqual(response.status_code, 200)
        checkin.refresh_from_db()
        self.assertEqual(checkin.status, DailyCheckIn.Status.COMPLETED)

    def test_duplicate_webhook_is_idempotent(self):
        _, prov = make_provider_user(email='p3msg@test.com')
        make_patient('+254700000203', provider=prov)
        payload = {
            'from': '+254700000203', 'to': '+254000000000',
            'text': 'YES', 'id': 'evt_dupe_001',
        }
        self.client.post('/api/messages/webhook/africastalking/', payload, format='json')
        response2 = self.client.post('/api/messages/webhook/africastalking/', payload, format='json')
        self.assertEqual(response2.status_code, 200)
        self.assertEqual(response2.data['status'], 'duplicate')

    def test_unknown_phone_returns_no_patient(self):
        response = self.client.post('/api/messages/webhook/africastalking/', {
            'from': '+254799999999', 'to': '+254000000000',
            'text': 'YES', 'id': 'evt_unknown_001',
        }, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['status'], 'no_patient')
