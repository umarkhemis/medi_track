from django.db import models
from django.conf import settings


class Alert(models.Model):
    class Severity(models.TextChoices):
        YELLOW = 'yellow', 'Yellow'
        RED = 'red', 'Red'

    class Status(models.TextChoices):
        OPEN = 'open', 'Open'
        ACKNOWLEDGED = 'acknowledged', 'Acknowledged'
        RESOLVED = 'resolved', 'Resolved'

    patient = models.ForeignKey(
        'patients.Patient', on_delete=models.CASCADE, related_name='alerts'
    )
    checkin = models.ForeignKey(
        'checkins.DailyCheckIn', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='alerts'
    )
    severity = models.CharField(max_length=10, choices=Severity.choices)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default='')
    triggered_by = models.CharField(max_length=255, blank=True, default='')

    assigned_to = models.ForeignKey(
        'providers.Provider', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='assigned_alerts'
    )
    acknowledged_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='acknowledged_alerts'
    )
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='resolved_alerts'
    )
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolution_notes = models.TextField(blank=True, default='')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'alerts'
        ordering = ['-created_at']

    def __str__(self):
        return f'[{self.severity.upper()}] {self.title} - {self.patient}'


class EscalationTask(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        IN_PROGRESS = 'in_progress', 'In Progress'
        COMPLETED = 'completed', 'Completed'
        CANCELLED = 'cancelled', 'Cancelled'

    alert = models.ForeignKey(Alert, on_delete=models.CASCADE, related_name='escalation_tasks')
    patient = models.ForeignKey(
        'patients.Patient', on_delete=models.CASCADE, related_name='escalation_tasks'
    )
    assigned_to = models.ForeignKey(
        'providers.Provider', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='escalation_tasks'
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    instructions = models.TextField(blank=True, default='')
    action_taken = models.TextField(blank=True, default='')
    due_by = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'escalation_tasks'
        ordering = ['-created_at']

    def __str__(self):
        return f'Escalation for {self.patient} [{self.status}]'
