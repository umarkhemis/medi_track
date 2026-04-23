from django.contrib import admin
from .models import Patient


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = [
        'get_full_name', 'phone_number_e164', 'condition',
        'current_risk_level', 'status', 'monitoring_active',
        'assigned_provider', 'discharge_date', 'created_at',
    ]
    list_filter = ['current_risk_level', 'status', 'monitoring_active', 'sms_opt_in', 'sex']
    search_fields = ['first_name', 'last_name', 'phone_number_e164', 'condition', 'external_reference']
    ordering = ['-created_at']
    readonly_fields = ['phone_number_e164', 'created_at', 'updated_at', 'created_by']

    fieldsets = (
        ('Identity', {'fields': ('first_name', 'middle_name', 'last_name', 'date_of_birth', 'sex')}),
        ('Contact', {'fields': ('phone_number_raw', 'phone_number_e164')}),
        ('Medical', {'fields': ('condition', 'secondary_conditions', 'medications')}),
        ('Discharge', {'fields': ('discharge_date', 'discharge_notes')}),
        ('Assignment', {'fields': ('assigned_provider', 'external_reference', 'created_by')}),
        ('Emergency Contact', {'fields': ('emergency_contact_name', 'emergency_contact_phone')}),
        ('Preferences', {'fields': ('preferred_check_in_time', 'preferred_language', 'timezone')}),
        ('Consent & SMS', {'fields': ('sms_opt_in', 'consent_at', 'consent_source')}),
        ('Monitoring', {'fields': ('monitoring_active', 'follow_up_end_date', 'current_risk_level', 'status')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )

    def get_full_name(self, obj):
        return obj.get_full_name()
    get_full_name.short_description = 'Full Name'
