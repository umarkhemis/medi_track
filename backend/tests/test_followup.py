import datetime
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status as http_status
from apps.messaging.models import FollowUpProgram, PatientProgramEnrollment
from .helpers import make_provider_user, make_patient


class FollowUpEnrollmentTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user, self.provider = make_provider_user(email='fu@test.com')
        self.patient = make_patient('+254700000400', provider=self.provider)
        self.program = FollowUpProgram.objects.create(
            name='14-Day Heart Failure Follow-Up',
            condition='heart failure',
            duration_days=14,
            check_in_questions=['chest_pain', 'shortness_of_breath'],
        )
        self.client.force_authenticate(user=self.user)

    def test_enrollment_creates_active_program_window(self):
        response = self.client.post(
            f'/api/patients/{self.patient.id}/enroll/',
            {'program_id': self.program.id},
            format='json',
        )
        self.assertEqual(response.status_code, http_status.HTTP_201_CREATED)
        enrollment = PatientProgramEnrollment.objects.filter(
            patient=self.patient, is_active=True
        ).first()
        self.assertIsNotNone(enrollment)
        self.assertEqual(enrollment.program, self.program)
        expected_end = datetime.date.today() + datetime.timedelta(days=14)
        self.assertEqual(enrollment.end_date, expected_end)

    def test_enrolling_new_program_deactivates_old(self):
        program2 = FollowUpProgram.objects.create(name='30-Day Follow-Up', duration_days=30)
        self.client.post(
            f'/api/patients/{self.patient.id}/enroll/',
            {'program_id': self.program.id}, format='json',
        )
        self.client.post(
            f'/api/patients/{self.patient.id}/enroll/',
            {'program_id': program2.id}, format='json',
        )
        active = PatientProgramEnrollment.objects.filter(patient=self.patient, is_active=True)
        self.assertEqual(active.count(), 1)
        self.assertEqual(active.first().program, program2)
