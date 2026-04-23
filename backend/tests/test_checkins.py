import datetime
from unittest.mock import patch
from django.test import TestCase
from django.utils import timezone
from apps.checkins.models import DailyCheckIn
from apps.checkins.scheduler import create_daily_checkins_for_date, send_due_checkins
from .helpers import make_provider_user, make_patient


class CheckInSchedulerTests(TestCase):
    def test_creates_one_checkin_per_patient_per_day(self):
        _, p1 = make_provider_user(email='p1@test.com')
        _, p2 = make_provider_user(email='p2@test.com')
        make_patient('+254700000101', provider=p1)
        make_patient('+254700000102', provider=p2)

        result = create_daily_checkins_for_date(datetime.date.today())
        self.assertEqual(result['created'], 2)
        self.assertEqual(DailyCheckIn.objects.count(), 2)

    def test_does_not_duplicate_checkin(self):
        _, prov = make_provider_user(email='p3@test.com')
        make_patient('+254700000103', provider=prov)
        create_daily_checkins_for_date(datetime.date.today())
        result = create_daily_checkins_for_date(datetime.date.today())
        self.assertEqual(result['created'], 0)
        self.assertEqual(result['skipped'], 1)

    def test_skips_opted_out_patient(self):
        _, prov = make_provider_user(email='p4@test.com')
        p = make_patient('+254700000104', provider=prov)
        p.sms_opt_in = False
        p.save()
        result = create_daily_checkins_for_date(datetime.date.today())
        self.assertEqual(result['created'], 0)

    @patch('apps.messaging.services.africastalking_service.AfricasTalkingService.send_sms')
    def test_due_checkins_are_sent(self, mock_send):
        mock_send.return_value = {'status': 'sent', 'message_id': 'AT123'}
        _, prov = make_provider_user(email='p5@test.com')
        patient = make_patient('+254700000105', provider=prov)

        checkin = DailyCheckIn.objects.create(
            patient=patient,
            scheduled_date=datetime.date.today(),
            scheduled_time=timezone.now() - datetime.timedelta(minutes=5),
            status=DailyCheckIn.Status.SCHEDULED,
            question_keys=['chest_pain'],
        )

        result = send_due_checkins()
        self.assertEqual(result['sent'], 1)
        checkin.refresh_from_db()
        self.assertEqual(checkin.status, DailyCheckIn.Status.SENT)
