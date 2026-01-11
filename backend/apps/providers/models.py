from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Provider(models.Model):
    """Healthcare provider model."""
    
    DEPARTMENT_CHOICES = [
        ('cardiology', 'Cardiology'),
        ('pulmonology', 'Pulmonology'),
        ('endocrinology', 'Endocrinology'),
        ('general', 'General Medicine'),
        ('nursing', 'Nursing'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='provider_profile')
    employee_id = models.CharField(max_length=50, unique=True)
    department = models.CharField(max_length=50, choices=DEPARTMENT_CHOICES)
    specialization = models.CharField(max_length=100, blank=True)
    license_number = models.CharField(max_length=50)
    is_available = models.BooleanField(default=True)
    max_patients = models.IntegerField(default=50)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'providers'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Dr. {self.user.get_full_name()} - {self.get_department_display()}"
    
    @property
    def current_patient_count(self):
        """Get count of active patients assigned to this provider."""
        return self.patients.filter(monitoring_active=True).count()
