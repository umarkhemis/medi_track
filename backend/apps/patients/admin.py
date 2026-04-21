from django.contrib import admin
from django.contrib import messages
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
    actions = ('trigger_followups_for_selected_patients',)
    
    fieldsets = (
        ('Patient Info', {
            'fields': ('user', 'date_of_birth')
        }),
        ('Provider Assignment (Optional)', {
            'fields': ('assigned_provider',)
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

    @admin.action(description='Trigger follow-up messages now for selected patients')
    def trigger_followups_for_selected_patients(self, request, queryset):
        from apps.messaging.services.followup_service import FollowUpSchedulerService

        stats = FollowUpSchedulerService().send_due_followups(
            patient_ids=list(queryset.values_list('id', flat=True)),
            force=True,
        )
        self.message_user(
            request,
            (
                f"Follow-up trigger complete. Attempted: {stats['attempted']}, "
                f"sent: {stats['sent']}, failed: {stats['failed']}, skipped: {stats['skipped']}"
            ),
            level=messages.INFO,
        )
