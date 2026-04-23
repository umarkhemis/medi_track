import datetime
from django.test import TestCase
from apps.checkins.models import DailyCheckIn
from apps.alerts.models import Alert, EscalationTask
from apps.alerts.risk_engine import evaluate_risk
from .helpers import make_provider_user, make_patient


def make_checkin(patient):
    return DailyCheckIn.objects.create(
        patient=patient,
        scheduled_date=datetime.date.today(),
        status=DailyCheckIn.Status.COMPLETED,
        question_keys=['chest_pain', 'shortness_of_breath', 'leg_swelling'],
    )


class RiskEngineTests(TestCase):
    def test_chest_pain_creates_red_alert_and_escalation(self):
        _, prov = make_provider_user(email='ra1@test.com')
        patient = make_patient('+254700000301', provider=prov)
        checkin = make_checkin(patient)
        evaluate_risk(patient, checkin, {'chest_pain': 'yes', 'medication_taken': 'yes'})

        patient.refresh_from_db()
        self.assertEqual(patient.current_risk_level, 'red')
        alert = Alert.objects.filter(patient=patient).first()
        self.assertIsNotNone(alert)
        self.assertEqual(alert.severity, 'red')
        self.assertEqual(alert.status, Alert.Status.OPEN)
        escalation = EscalationTask.objects.filter(patient=patient).first()
        self.assertIsNotNone(escalation)
        self.assertEqual(escalation.status, EscalationTask.Status.PENDING)

    def test_sob_and_swelling_creates_yellow_alert(self):
        _, prov = make_provider_user(email='ra2@test.com')
        patient = make_patient('+254700000302', provider=prov)
        checkin = make_checkin(patient)
        evaluate_risk(patient, checkin, {'shortness_of_breath': 'yes', 'leg_swelling': 'yes'})
        patient.refresh_from_db()
        self.assertEqual(patient.current_risk_level, 'yellow')
        alert = Alert.objects.filter(patient=patient).first()
        self.assertEqual(alert.severity, 'yellow')
        self.assertEqual(EscalationTask.objects.filter(patient=patient).count(), 0)

    def test_no_symptoms_stays_green(self):
        _, prov = make_provider_user(email='ra3@test.com')
        patient = make_patient('+254700000303', provider=prov)
        checkin = make_checkin(patient)
        evaluate_risk(patient, checkin, {'chest_pain': 'no', 'medication_taken': 'yes'})
        patient.refresh_from_db()
        self.assertEqual(patient.current_risk_level, 'green')
        self.assertEqual(Alert.objects.filter(patient=patient).count(), 0)

    def test_copd_breathlessness_and_inhaler_creates_red(self):
        _, prov = make_provider_user(email='ra4@test.com')
        patient = make_patient('+254700000304', condition='COPD', provider=prov)
        checkin = make_checkin(patient)
        evaluate_risk(patient, checkin, {'breathlessness': 'yes', 'rescue_inhaler_use': 'yes'})
        patient.refresh_from_db()
        self.assertEqual(patient.current_risk_level, 'red')
        self.assertEqual(EscalationTask.objects.filter(patient=patient).count(), 1)
