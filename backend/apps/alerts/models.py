from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Alert(models.Model):
    """Alert model for patient risk notifications."""
    
    ALERT_TYPE_CHOICES = [
        ('yellow', 'Yellow Alert - Moderate Risk'),
        ('red', 'Red Alert - High Risk'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('acknowledged', 'Acknowledged'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('escalated', 'Escalated'),
    ]
    
    patient = models.ForeignKey('patients.Patient', on_delete=models.CASCADE, related_name='alerts')
    checkin = models.ForeignKey(
        'checkins.DailyCheckIn',
        on_delete=models.SET_NULL,
        null=True,
        related_name='alerts'
    )
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    trigger_reason = models.TextField()  # What triggered the alert
    risk_score = models.IntegerField()
    acknowledged_by = models.ForeignKey(
        'providers.Provider',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='acknowledged_alerts'
    )
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    action_taken = models.TextField(blank=True)
    resolved_by = models.ForeignKey(
        'providers.Provider',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resolved_alerts'
    )
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolution_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'alerts'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_alert_type_display()} - {self.patient.user.get_full_name()}"
