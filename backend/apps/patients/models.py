from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Patient(models.Model):
    """Patient model for post-discharge monitoring."""
    
    CONDITION_CHOICES = [
        ('heart_failure', 'Heart Failure'),
        ('copd', 'COPD'),
        ('diabetes', 'Diabetes'),
        ('hypertension', 'Hypertension'),
        ('pneumonia', 'Pneumonia'),
        ('other', 'Other'),
    ]
    
    RISK_LEVEL_CHOICES = [
        ('green', 'Low Risk'),
        ('yellow', 'Moderate Risk'),
        ('red', 'High Risk'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='patient_profile')
    date_of_birth = models.DateField()
    condition = models.CharField(max_length=50, choices=CONDITION_CHOICES)
    secondary_conditions = models.JSONField(default=list, blank=True)
    discharge_date = models.DateField()
    discharge_notes = models.TextField(blank=True)
    medications = models.JSONField(default=list)  # List of medications
    assigned_provider = models.ForeignKey(
        'providers.Provider',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='patients'
    )
    emergency_contact_name = models.CharField(max_length=100)
    emergency_contact_phone = models.CharField(max_length=20)
    current_risk_level = models.CharField(max_length=10, choices=RISK_LEVEL_CHOICES, default='green')
    preferred_check_in_time = models.TimeField(default='09:00')
    monitoring_active = models.BooleanField(default=True)
    follow_up_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'patients'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.get_condition_display()}"
    
    @property
    def days_since_discharge(self):
        """Calculate days since discharge."""
        if self.discharge_date is None:
            return None
        from datetime import date
        return (date.today() - self.discharge_date).days
