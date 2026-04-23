from django.contrib import admin
from .models import Alert, EscalationTask


class EscalationTaskInline(admin.TabularInline):
    model = EscalationTask
    extra = 0
    readonly_fields = ['created_at', 'completed_at']


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = [
        'patient', 'severity', 'status', 'title',
        'assigned_to', 'acknowledged_at', 'resolved_at', 'created_at',
    ]
    list_filter = ['severity', 'status']
    search_fields = ['patient__first_name', 'patient__last_name', 'title']
    readonly_fields = ['created_at', 'updated_at', 'acknowledged_at', 'resolved_at']
    ordering = ['-created_at']
    inlines = [EscalationTaskInline]


@admin.register(EscalationTask)
class EscalationTaskAdmin(admin.ModelAdmin):
    list_display = ['patient', 'status', 'assigned_to', 'due_by', 'completed_at', 'created_at']
    list_filter = ['status']
    search_fields = ['patient__first_name', 'patient__last_name']
    readonly_fields = ['created_at', 'completed_at']
    ordering = ['-created_at']
