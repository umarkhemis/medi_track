from django.test import TestCase
from datetime import date
from unittest.mock import patch
from django.core.management import call_command
from django.utils import timezone

from apps.messaging.models import FollowUpSchedule, Message, MessageTemplate
from apps.messaging.services.followup_service import FollowUpSchedulerService
from apps.patients.models import Patient


class FollowUpSchedulerServiceTests(TestCase):
    def setUp(self):
        self.patient = Patient.objects.create(
            first_name='Alice',
            last_name='Patient',
            phone_number_raw='0700000010',
            phone_number_e164='+254700000010',
            date_of_birth=date(1992, 2, 2),
            condition='diabetes',
            discharge_date=timezone.localdate(),
            preferred_check_in_time=(timezone.now() - timezone.timedelta(minutes=30)).time(),
            medications='',
            emergency_contact_name='Bob',
            emergency_contact_phone='+254700000011',
        )
        self.template = MessageTemplate.objects.create(
            name='Follow-up Template',
            template_type='reminder',
            body='Hi {first_name}, this is your follow-up.',
            is_active=True,
        )
        self.schedule = FollowUpSchedule.objects.create(
            name='5 minute follow-up',
            template=self.template,
            interval_value=5,
            interval_unit='minutes',
            is_active=True,
        )

    @patch('apps.messaging.services.followup_service.AfricasTalkingService.send_message')
    def test_send_due_followups_creates_message_for_due_schedule(self, mock_send_message):
        mock_send_message.return_value = {'success': True, 'sid': 'MSG123'}

        stats = FollowUpSchedulerService().send_due_followups()

        self.assertEqual(stats['attempted'], 1)
        self.assertEqual(stats['sent'], 1)
        message = Message.objects.get(follow_up_schedule=self.schedule, patient=self.patient)
        self.assertEqual(message.status, 'sent')
        self.assertEqual(message.follow_up_trigger_at.date(), timezone.localdate())
        self.assertEqual(message.provider_message_id, 'MSG123')

    @patch('apps.messaging.services.followup_service.AfricasTalkingService.send_message')
    def test_followup_is_not_sent_twice_for_same_patient_and_schedule(self, mock_send_message):
        mock_send_message.return_value = {'success': True, 'sid': 'MSG123'}

        service = FollowUpSchedulerService()
        service.send_due_followups()
        second_stats = service.send_due_followups()

        self.assertEqual(Message.objects.filter(follow_up_schedule=self.schedule).count(), 1)
        self.assertEqual(second_stats['attempted'], 0)

    @patch('apps.messaging.services.followup_service.AfricasTalkingService.send_message')
    def test_send_followups_management_command_runs(self, mock_send_message):
        mock_send_message.return_value = {'success': True, 'sid': 'CMD123'}

        call_command('send_followups')

        self.assertTrue(Message.objects.filter(follow_up_schedule=self.schedule).exists())
