from django.contrib import admin
from .models import Patient


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    """Admin interface for Patient model."""
    
    list_display = (
        'user', 'condition', 'current_risk_level', 'discharge_date',
        'assigned_provider', 'monitoring_active', 'days_since_discharge'
    )
    list_filter = ('condition', 'current_risk_level', 'monitoring_active', 'discharge_date')
    search_fields = ('user__first_name', 'user__last_name', 'user__email', 'emergency_contact_name')
    ordering = ('-current_risk_level', '-discharge_date')
    readonly_fields = ('created_at', 'updated_at', 'days_since_discharge')
    
    fieldsets = (
        ('Patient Info', {
            'fields': ('user', 'date_of_birth', 'assigned_provider')
        }),
        ('Medical Info', {
            'fields': (
                'condition', 'secondary_conditions', 'discharge_date',
                'discharge_notes', 'medications', 'current_risk_level'
            )
        }),
        ('Monitoring', {
            'fields': (
                'monitoring_active', 'preferred_check_in_time', 'follow_up_date'
            )
        }),
        ('Emergency Contact', {
            'fields': ('emergency_contact_name', 'emergency_contact_phone')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'days_since_discharge')
        }),
    )
