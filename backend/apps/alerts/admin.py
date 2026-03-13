from django.contrib import admin
from .models import Alert


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    """Admin interface for Alert model."""
    
    list_display = (
        'patient', 'alert_type', 'status', 'risk_score',
        'acknowledged_by', 'resolved_by', 'created_at'
    )
    list_filter = ('alert_type', 'status', 'created_at')
    search_fields = ('patient__user__first_name', 'patient__user__last_name', 'trigger_reason')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at', 'acknowledged_at', 'resolved_at')
    
    fieldsets = (
        ('Alert Info', {
            'fields': ('patient', 'checkin', 'alert_type', 'status', 'risk_score', 'trigger_reason')
        }),
        ('Acknowledgment', {
            'fields': ('acknowledged_by', 'acknowledged_at', 'action_taken')
        }),
        ('Resolution', {
            'fields': ('resolved_by', 'resolved_at', 'resolution_notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
