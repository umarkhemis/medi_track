from django.db import models
from django.conf import settings


class Patient(models.Model):
    class RiskLevel(models.TextChoices):
        GREEN = 'green', 'Green'
        YELLOW = 'yellow', 'Yellow'
        RED = 'red', 'Red'

    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        PAUSED = 'paused', 'Paused'
        COMPLETED = 'completed', 'Completed'
        OPTED_OUT = 'opted_out', 'Opted Out'
        UNREACHABLE = 'unreachable', 'Unreachable'

    class Sex(models.TextChoices):
        MALE = 'male', 'Male'
        FEMALE = 'female', 'Female'
        OTHER = 'other', 'Other'
        UNKNOWN = 'unknown', 'Unknown'

    # Identity
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    middle_name = models.CharField(max_length=150, blank=True, default='')
    date_of_birth = models.DateField(null=True, blank=True)
    sex = models.CharField(max_length=10, choices=Sex.choices, default=Sex.UNKNOWN)

    # Contact
    phone_number_raw = models.CharField(max_length=30)
    phone_number_e164 = models.CharField(max_length=20, unique=True, db_index=True)

    # Medical
    condition = models.CharField(max_length=255)
    secondary_conditions = models.TextField(blank=True, default='')
    medications = models.TextField(blank=True, default='')

    # Discharge
    discharge_date = models.DateField(null=True, blank=True)
    discharge_notes = models.TextField(blank=True, default='')

    # Assignment
    assigned_provider = models.ForeignKey(
        'providers.Provider',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='patients',
    )
    external_reference = models.CharField(max_length=100, blank=True, default='')

    # Emergency contact
    emergency_contact_name = models.CharField(max_length=255, blank=True, default='')
    emergency_contact_phone = models.CharField(max_length=30, blank=True, default='')

    # Preferences
    preferred_check_in_time = models.TimeField(null=True, blank=True)
    preferred_language = models.CharField(max_length=10, default='en')
    timezone = models.CharField(max_length=50, default='UTC')

    # Consent & SMS
    sms_opt_in = models.BooleanField(default=True)
    consent_at = models.DateTimeField(null=True, blank=True)
    consent_source = models.CharField(max_length=100, blank=True, default='')

    # Monitoring
    monitoring_active = models.BooleanField(default=True)
    follow_up_end_date = models.DateField(null=True, blank=True)
    current_risk_level = models.CharField(
        max_length=10, choices=RiskLevel.choices, default=RiskLevel.GREEN
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)

    # Meta
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_patients',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'patients'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.get_full_name()} ({self.phone_number_e164})'

    def get_full_name(self):
        parts = [self.first_name, self.middle_name, self.last_name]
        return ' '.join(p for p in parts if p).strip()

    def pause_monitoring(self):
        self.monitoring_active = False
        self.status = self.Status.PAUSED
        self.save(update_fields=['monitoring_active', 'status', 'updated_at'])

    def resume_monitoring(self):
        self.monitoring_active = True
        self.status = self.Status.ACTIVE
        self.save(update_fields=['monitoring_active', 'status', 'updated_at'])

    def opt_out(self):
        self.sms_opt_in = False
        self.monitoring_active = False
        self.status = self.Status.OPTED_OUT
        self.save(update_fields=['sms_opt_in', 'monitoring_active', 'status', 'updated_at'])

    def mark_unreachable(self):
        self.status = self.Status.UNREACHABLE
        self.monitoring_active = False
        self.save(update_fields=['status', 'monitoring_active', 'updated_at'])
