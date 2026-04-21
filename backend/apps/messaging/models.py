from django.db import models
from django.utils import timezone


class MessageTemplate(models.Model):
    """Template for automated messages."""
    
    TEMPLATE_TYPE_CHOICES = [
        ('welcome', 'Welcome Message'),
        ('daily_checkin', 'Daily Check-in'),
        ('reminder', 'Check-in Reminder'),
        ('alert_response', 'Alert Response'),
        ('follow_up', 'Follow-up'),
        ('custom', 'Custom Message'),
    ]
    
    CONDITION_CHOICES = [
        ('all', 'All Conditions'),
        ('heart_failure', 'Heart Failure'),
        ('copd', 'COPD'),
        ('diabetes', 'Diabetes'),
        ('hypertension', 'Hypertension'),
    ]
    
    name = models.CharField(max_length=100)
    template_type = models.CharField(max_length=50, choices=TEMPLATE_TYPE_CHOICES)
    condition = models.CharField(max_length=50, choices=CONDITION_CHOICES, default='all')
    content = models.TextField()  # Can include placeholders like {patient_name}
    questions = models.JSONField(default=list)  # For check-in templates
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'message_templates'
        ordering = ['template_type', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.get_template_type_display()})"


class Message(models.Model):
    """Message sent to or received from patients."""
    
    CHANNEL_CHOICES = [
        ('sms', 'SMS'),
        ('whatsapp', 'WhatsApp'),
    ]
    
    DIRECTION_CHOICES = [
        ('outbound', 'Outbound'),
        ('inbound', 'Inbound'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('read', 'Read'),
        ('failed', 'Failed'),
    ]
    
    patient = models.ForeignKey('patients.Patient', on_delete=models.CASCADE, related_name='messages')
    provider = models.ForeignKey(
        'providers.Provider',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    channel = models.CharField(max_length=20, choices=CHANNEL_CHOICES)
    direction = models.CharField(max_length=20, choices=DIRECTION_CHOICES)
    content = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    message_sid = models.CharField(max_length=100, blank=True)  # Provider message ID (e.g. Africa's Talking)
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    is_automated = models.BooleanField(default=False)
    related_checkin = models.ForeignKey(
        'checkins.DailyCheckIn',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'messages'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_direction_display()} {self.get_channel_display()} - {self.patient.user.get_full_name()}"
