from django.db import models
from django.conf import settings


class Provider(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='provider_profile',
    )
    specialization = models.CharField(max_length=200, blank=True, default='')
    facility_name = models.CharField(max_length=255, blank=True, default='')
    department = models.CharField(max_length=200, blank=True, default='')
    timezone = models.CharField(max_length=50, default='UTC')
    is_active = models.BooleanField(default=True)
    is_available = models.BooleanField(default=True)
    max_patients = models.PositiveIntegerField(default=50)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'providers'
        ordering = ['user__last_name']

    def __str__(self):
        return f'Dr. {self.user.get_full_name()} ({self.facility_name})'

    @property
    def patient_count(self):
        return self.patients.filter(monitoring_active=True).count()

    @property
    def full_name(self):
        return self.user.get_full_name()
