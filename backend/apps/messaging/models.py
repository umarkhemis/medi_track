from django.db import models
from django.conf import settings


class Message(models.Model):
    class Channel(models.TextChoices):
        SMS = 'sms', 'SMS'

    class Direction(models.TextChoices):
        OUTBOUND = 'outbound', 'Outbound'
        INBOUND = 'inbound', 'Inbound'

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        SENT = 'sent', 'Sent'
        DELIVERED = 'delivered', 'Delivered'
        FAILED = 'failed', 'Failed'
        RECEIVED = 'received', 'Received'

    patient = models.ForeignKey(
        'patients.Patient', on_delete=models.CASCADE, related_name='messages'
    )
    provider = models.ForeignKey(
        'providers.Provider', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='sent_messages'
    )
    channel = models.CharField(max_length=10, choices=Channel.choices, default=Channel.SMS)
    direction = models.CharField(max_length=10, choices=Direction.choices)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    body = models.TextField()
    is_automated = models.BooleanField(default=True)

    to_number = models.CharField(max_length=20, blank=True, default='')
    from_number = models.CharField(max_length=20, blank=True, default='')
    provider_message_id = models.CharField(max_length=255, blank=True, default='', db_index=True)
    external_status = models.CharField(max_length=50, blank=True, default='')
    error_code = models.CharField(max_length=50, blank=True, default='')
    error_message = models.TextField(blank=True, default='')

    dedupe_key = models.CharField(max_length=255, blank=True, default='', db_index=True)
    raw_payload = models.JSONField(null=True, blank=True)

    checkin = models.ForeignKey(
        'checkins.DailyCheckIn', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='messages'
    )
    follow_up_schedule = models.ForeignKey(
        'messaging.FollowUpSchedule', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='messages'
    )
    follow_up_trigger_at = models.DateTimeField(null=True, blank=True)

    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    received_at = models.DateTimeField(null=True, blank=True)
    failed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'messages'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.direction} | {self.patient} | {self.status}'


class DeliveryReceipt(models.Model):
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='delivery_receipts')
    provider_message_id = models.CharField(max_length=255, db_index=True)
    status = models.CharField(max_length=50)
    failure_reason = models.CharField(max_length=255, blank=True, default='')
    raw_payload = models.JSONField(null=True, blank=True)
    received_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'delivery_receipts'

    def __str__(self):
        return f'Receipt {self.provider_message_id} - {self.status}'


class InboundWebhookEvent(models.Model):
    event_id = models.CharField(max_length=255, unique=True, db_index=True)
    from_number = models.CharField(max_length=20)
    to_number = models.CharField(max_length=20, blank=True, default='')
    body = models.TextField()
    raw_payload = models.JSONField(null=True, blank=True)
    processed = models.BooleanField(default=False)
    error = models.TextField(blank=True, default='')
    received_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'inbound_webhook_events'
        ordering = ['-received_at']

    def __str__(self):
        return f'Inbound {self.from_number} at {self.received_at}'


class MessageTemplate(models.Model):
    class TemplateType(models.TextChoices):
        CHECKIN = 'checkin', 'Check-in'
        REMINDER = 'reminder', 'Reminder'
        ALERT = 'alert', 'Alert'
        WELCOME = 'welcome', 'Welcome'
        GENERAL = 'general', 'General'

    name = models.CharField(max_length=200)
    template_type = models.CharField(max_length=20, choices=TemplateType.choices)
    condition = models.CharField(max_length=200, blank=True, default='')
    language = models.CharField(max_length=10, default='en')
    body = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'message_templates'

    def __str__(self):
        return f'{self.name} ({self.template_type})'


class FollowUpSchedule(models.Model):
    class IntervalUnit(models.TextChoices):
        MINUTES = 'minutes', 'Minutes'
        HOURS = 'hours', 'Hours'
        DAYS = 'days', 'Days'

    name = models.CharField(max_length=200)
    template = models.ForeignKey(
        MessageTemplate, on_delete=models.CASCADE, related_name='follow_up_schedules'
    )
    interval_value = models.PositiveIntegerField()
    interval_unit = models.CharField(max_length=10, choices=IntervalUnit.choices, default='days')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'follow_up_schedules'
        ordering = ['interval_value', 'id']

    def __str__(self):
        return f'{self.name} ({self.interval_value} {self.interval_unit})'


class FollowUpProgram(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, default='')
    condition = models.CharField(max_length=200, blank=True, default='')
    duration_days = models.PositiveIntegerField(null=True, blank=True)
    check_in_questions = models.JSONField(default=list)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'follow_up_programs'

    def __str__(self):
        return self.name


class PatientProgramEnrollment(models.Model):
    patient = models.ForeignKey(
        'patients.Patient', on_delete=models.CASCADE, related_name='enrollments'
    )
    program = models.ForeignKey(FollowUpProgram, on_delete=models.CASCADE, related_name='enrollments')
    enrolled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    enrolled_at = models.DateTimeField(auto_now_add=True)
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'patient_program_enrollments'
        ordering = ['-enrolled_at']

    def __str__(self):
        return f'{self.patient} -> {self.program}'
