"""
Risk assessment service for calculating patient risk scores based on check-in responses.
"""

from django.utils import timezone
from apps.alerts.models import Alert


class RiskAssessmentService:
    """Service for calculating risk scores and generating alerts."""
    
    # Symptom weights by condition
    # Higher weight = more critical symptom for that condition
    SYMPTOM_WEIGHTS = {
        'heart_failure': {
            'shortness_of_breath': 2.5,
            'swelling': 1.8,
            'weight_gain': 1.8,
            'fatigue': 1.2,
            'chest_pain': 3.0,
            'palpitations': 1.5,
            'dizziness': 1.3,
        },
        'copd': {
            'shortness_of_breath': 2.5,
            'cough_severity': 1.8,
            'mucus_production': 1.2,
            'wheezing': 1.8,
            'chest_tightness': 1.5,
            'fatigue': 1.0,
        },
        'diabetes': {
            'blood_sugar_high': 2.5,
            'blood_sugar_low': 3.0,
            'medication_missed': 2.0,
            'dizziness': 1.5,
            'excessive_thirst': 1.3,
            'frequent_urination': 1.2,
            'blurred_vision': 1.8,
        },
        'hypertension': {
            'blood_pressure_high': 2.5,
            'headache': 1.5,
            'dizziness': 1.8,
            'chest_pain': 2.5,
            'vision_changes': 2.0,
            'medication_missed': 2.0,
        },
        'pneumonia': {
            'fever': 2.0,
            'cough_severity': 1.8,
            'shortness_of_breath': 2.5,
            'chest_pain': 2.0,
            'fatigue': 1.2,
            'confusion': 2.5,
        },
    }
    
    # Default weights if condition not found
    DEFAULT_WEIGHTS = {
        'pain_level': 1.5,
        'fatigue': 1.0,
        'medication_adherence': 2.0,
        'mobility': 1.2,
        'appetite': 0.8,
    }
    
    def calculate_risk_score(self, checkin):
        """
        Calculate risk score from check-in responses.
        
        Args:
            checkin: DailyCheckIn instance
            
        Returns:
            float: Risk score on 0-10 scale
        """
        patient = checkin.patient
        responses = checkin.responses.all()
        
        # Get condition-specific weights
        weights = self.SYMPTOM_WEIGHTS.get(
            patient.condition,
            self.DEFAULT_WEIGHTS
        )
        
        if not responses.exists():
            return 0.0
        
        total_score = 0
        total_weight = 0
        
        for response in responses:
            weight = weights.get(response.question_key, 1.0)
            # response_score is expected to be 0-10
            total_score += response.response_score * weight
            total_weight += weight * 10  # Max possible score per question is 10
        
        if total_weight == 0:
            return 0.0
        
        # Normalize to 0-10 scale
        normalized_score = (total_score / total_weight) * 10
        
        return round(min(10.0, max(0.0, normalized_score)), 1)
    
    def get_risk_level(self, score):
        """
        Determine risk level from score.
        
        Args:
            score (float): Risk score (0-10)
            
        Returns:
            str: Risk level ('green', 'yellow', or 'red')
        """
        if score <= 3.0:
            return 'green'
        elif score <= 6.5:
            return 'yellow'
        else:
            return 'red'
    
    def process_checkin(self, checkin):
        """
        Process completed check-in: calculate risk and generate alerts if needed.
        
        Args:
            checkin: DailyCheckIn instance
            
        Returns:
            dict: Processing results with score, risk level, and alert info
        """
        # Calculate risk score
        score = self.calculate_risk_score(checkin)
        risk_level = self.get_risk_level(score)
        
        # Update check-in record
        checkin.risk_score = score
        checkin.risk_level = risk_level
        checkin.status = 'completed'
        checkin.completed_at = timezone.now()
        checkin.save()
        
        # Update patient's current risk level
        patient = checkin.patient
        patient.current_risk_level = risk_level
        patient.save()
        
        # Generate alert if necessary
        alert_created = False
        alert_id = None
        
        if risk_level in ['yellow', 'red']:
            alert = self.create_alert(checkin, risk_level, score)
            alert_created = True
            alert_id = alert.id
        
        return {
            'score': score,
            'risk_level': risk_level,
            'alert_created': alert_created,
            'alert_id': alert_id
        }
    
    def create_alert(self, checkin, risk_level, score):
        """
        Create an alert for elevated risk.
        
        Args:
            checkin: DailyCheckIn instance
            risk_level (str): 'yellow' or 'red'
            score (float): Risk score
            
        Returns:
            Alert: Created alert instance
        """
        patient = checkin.patient
        
        # Build trigger reason from concerning responses
        concerning_symptoms = []
        for response in checkin.responses.filter(response_score__gte=7):
            concerning_symptoms.append(
                f"{response.question_text}: {response.response_value}/10"
            )
        
        trigger_reason = "; ".join(concerning_symptoms) if concerning_symptoms else \
                        f"Elevated risk score detected ({score}/10)"
        
        # Determine alert type
        alert_type = 'red' if risk_level == 'red' else 'yellow'
        
        # Create alert
        alert = Alert.objects.create(
            patient=patient,
            checkin=checkin,
            alert_type=alert_type,
            risk_score=int(score),
            trigger_reason=trigger_reason,
            status='active'
        )
        
        return alert
    
    def parse_response_value(self, response_text, question_key):
        """
        Parse patient response and convert to score (0-10).
        
        Args:
            response_text (str): Patient's response text
            question_key (str): Type of question
            
        Returns:
            tuple: (parsed_value, score)
        """
        response_text = response_text.strip().upper()
        
        # Try to parse as number
        try:
            value = float(response_text)
            if 0 <= value <= 10:
                return (str(int(value)), int(value))
        except (ValueError, TypeError):
            pass
        
        # Parse YES/NO responses
        if response_text in ['YES', 'Y']:
            return ('YES', 8)  # YES to symptom = high score
        elif response_text in ['NO', 'N']:
            return ('NO', 2)  # NO to symptom = low score
        
        # Parse severity words
        severity_map = {
            'NONE': 0,
            'MINIMAL': 2,
            'MILD': 3,
            'SLIGHT': 3,
            'MODERATE': 5,
            'MEDIUM': 5,
            'SEVERE': 8,
            'EXTREME': 10,
            'VERY': 8,
        }
        
        for word, score in severity_map.items():
            if word in response_text:
                return (response_text, score)
        
        # Default: assume it's a number if single token
        if response_text.isdigit():
            value = int(response_text)
            return (str(value), min(10, value))
        
        # Unable to parse, return neutral
        return (response_text, 5)
