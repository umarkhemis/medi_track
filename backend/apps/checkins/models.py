from django.db import models
from django.utils import timezone


class DailyCheckIn(models.Model):
    class Status(models.TextChoices):
        SCHEDULED = 'scheduled', 'Scheduled'
        SENT = 'sent', 'Sent'
        REMINDED = 'reminded', 'Reminded'
        COMPLETED = 'completed', 'Completed'
        MISSED = 'missed', 'Missed'
        SKIPPED = 'skipped', 'Skipped'

    patient = models.ForeignKey(
        'patients.Patient',
        on_delete=models.CASCADE,
        related_name='checkins',
    )
    scheduled_date = models.DateField()
    scheduled_time = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SCHEDULED)

    question_keys = models.JSONField(default=list)
    response_data = models.JSONField(null=True, blank=True)

    sent_time = models.DateTimeField(null=True, blank=True)
    expiration_time = models.DateTimeField(null=True, blank=True)
    completed_time = models.DateTimeField(null=True, blank=True)
    missed_time = models.DateTimeField(null=True, blank=True)

    attempt_count = models.PositiveIntegerField(default=0)
    reminder_count = models.PositiveIntegerField(default=0)
    last_attempt_time = models.DateTimeField(null=True, blank=True)

    provider_message_id = models.CharField(max_length=255, blank=True, default='')
    correlation_id = models.CharField(max_length=255, blank=True, default='', db_index=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'daily_checkins'
        ordering = ['-scheduled_date', '-created_at']
        unique_together = [('patient', 'scheduled_date')]

    def __str__(self):
        return f'CheckIn {self.patient} {self.scheduled_date} [{self.status}]'

    def mark_sent(self, message_id=''):
        self.status = self.Status.SENT
        self.sent_time = timezone.now()
        self.attempt_count += 1
        self.last_attempt_time = timezone.now()
        self.provider_message_id = message_id
        # Expire after 12 hours
        import datetime
        self.expiration_time = timezone.now() + datetime.timedelta(hours=12)
        self.save()

    def mark_reminded(self, message_id=''):
        self.status = self.Status.REMINDED
        self.reminder_count += 1
        self.last_attempt_time = timezone.now()
        if message_id:
            self.provider_message_id = message_id
        self.save()

    def mark_missed(self):
        self.status = self.Status.MISSED
        self.missed_time = timezone.now()
        self.save(update_fields=['status', 'missed_time', 'updated_at'])

    @property
    def is_expired(self):
        if self.expiration_time:
            return timezone.now() > self.expiration_time
        return False


class CheckInResponse(models.Model):
    checkin = models.ForeignKey(
        DailyCheckIn,
        on_delete=models.CASCADE,
        related_name='responses',
    )
    patient = models.ForeignKey(
        'patients.Patient',
        on_delete=models.CASCADE,
        related_name='checkin_responses',
    )
    question_key = models.CharField(max_length=100)
    response_value = models.CharField(max_length=255)
    raw_response_text = models.TextField(blank=True, default='')
    source_message = models.ForeignKey(
        'messaging.Message',
        on_delete=models.SET_NULL,
        null=True, blank=True,
    )
    received_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'checkin_responses'
        ordering = ['received_at']

    def __str__(self):
        return f'{self.patient} | {self.question_key}: {self.response_value}'
