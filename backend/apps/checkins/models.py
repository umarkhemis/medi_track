from django.db import models
from django.utils import timezone


class DailyCheckIn(models.Model):
    """Daily check-in record for patients."""
    
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('sent', 'Sent'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('missed', 'Missed'),
    ]
    
    patient = models.ForeignKey('patients.Patient', on_delete=models.CASCADE, related_name='checkins')
    scheduled_date = models.DateField()
    scheduled_time = models.TimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    sent_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    risk_score = models.IntegerField(null=True, blank=True)  # 0-10 scale
    risk_level = models.CharField(max_length=10, null=True, blank=True)  # green/yellow/red
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'daily_checkins'
        unique_together = ['patient', 'scheduled_date']
        ordering = ['-scheduled_date', '-scheduled_time']
    
    def __str__(self):
        return f"{self.patient.user.get_full_name()} - {self.scheduled_date}"


class CheckInResponse(models.Model):
    """Individual question responses within a check-in."""
    
    checkin = models.ForeignKey(DailyCheckIn, on_delete=models.CASCADE, related_name='responses')
    question_key = models.CharField(max_length=50)  # e.g., 'shortness_of_breath', 'swelling'
    question_text = models.TextField()
    response_value = models.CharField(max_length=255)  # Could be '7', 'YES', etc.
    response_score = models.IntegerField(default=0)  # Normalized score for risk calculation
    responded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'checkin_responses'
        ordering = ['responded_at']
    
    def __str__(self):
        return f"{self.checkin} - {self.question_key}: {self.response_value}"
