from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from apps.patients.models import Patient
from .helpers import make_provider_user, make_patient


class PatientCreationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user, self.provider = make_provider_user()
        self.client.force_authenticate(user=self.user)

    def test_provider_can_create_patient_without_auth_user(self):
        data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'phone_number_raw': '+254700000001',
            'condition': 'Heart Failure',
            'discharge_date': '2024-01-15',
        }
        response = self.client.post('/api/patients/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        patient = Patient.objects.get(pk=response.data['id'])
        self.assertEqual(patient.phone_number_e164, '+254700000001')
        self.assertEqual(patient.assigned_provider, self.provider)

    def test_duplicate_phone_is_rejected(self):
        make_patient('+254700000002', provider=self.provider)
        data = {
            'first_name': 'Another',
            'last_name': 'Person',
            'phone_number_raw': '+254700000002',
            'condition': 'COPD',
        }
        response = self.client.post('/api/patients/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_phone_is_rejected(self):
        data = {
            'first_name': 'Bad',
            'last_name': 'Phone',
            'phone_number_raw': 'notaphone',
            'condition': 'COPD',
        }
        response = self.client.post('/api/patients/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_provider_cannot_see_other_providers_patients(self):
        user2, provider2 = make_provider_user(email='other@test.com')
        make_patient('+254700000010', provider=provider2)
        response = self.client.get('/api/patients/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 0)

    def test_patient_opt_out(self):
        patient = make_patient('+254700000020', provider=self.provider)
        response = self.client.post(f'/api/patients/{patient.id}/opt_out/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        patient.refresh_from_db()
        self.assertFalse(patient.sms_opt_in)
        self.assertEqual(patient.status, Patient.Status.OPTED_OUT)

    def test_patient_pause_and_resume(self):
        patient = make_patient('+254700000021', provider=self.provider)
        self.client.post(f'/api/patients/{patient.id}/pause_monitoring/')
        patient.refresh_from_db()
        self.assertFalse(patient.monitoring_active)
        self.client.post(f'/api/patients/{patient.id}/resume_monitoring/')
        patient.refresh_from_db()
        self.assertTrue(patient.monitoring_active)
