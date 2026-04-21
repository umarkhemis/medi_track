from django.test import TestCase
from datetime import date
from django.contrib.auth import get_user_model

from apps.patients.models import Patient


class PatientModelTests(TestCase):
    def test_patient_can_be_created_without_assigned_provider(self):
        user = get_user_model().objects.create_user(
            username='patient-without-provider',
            password='testpass123',
            role='patient',
            phone_number='+254700000001',
            first_name='Test',
            last_name='Patient',
        )

        patient = Patient.objects.create(
            user=user,
            date_of_birth=date(1990, 1, 1),
            condition='diabetes',
            discharge_date=date.today(),
            medications=[],
            emergency_contact_name='Jane Doe',
            emergency_contact_phone='+254700000002',
        )

        self.assertIsNone(patient.assigned_provider)
