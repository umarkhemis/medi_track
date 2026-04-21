from django.contrib import admin
from django.contrib import messages

from .models import MessageTemplate, Message, FollowUpSchedule


@admin.register(MessageTemplate)
class MessageTemplateAdmin(admin.ModelAdmin):
    """Admin interface for MessageTemplate model."""
    
    list_display = ('name', 'template_type', 'condition', 'is_active', 'created_at')
    list_filter = ('template_type', 'condition', 'is_active')
    search_fields = ('name', 'content')
    ordering = ('-created_at',)
    readonly_fields = ('created_at',)


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    """Admin interface for Message model."""
    
    list_display = (
        'patient', 'channel', 'direction', 'status',
        'follow_up_schedule', 'is_automated', 'created_at', 'sent_at'
    )
    list_filter = (
        'channel',
        'direction',
        'status',
        'is_automated',
        'follow_up_schedule',
        'created_at',
    )
    search_fields = ('patient__user__first_name', 'patient__user__last_name', 'content')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'sent_at', 'delivered_at', 'read_at', 'message_sid')


@admin.register(FollowUpSchedule)
class FollowUpScheduleAdmin(admin.ModelAdmin):
    """Admin interface for follow-up scheduling."""

    list_display = (
        'name',
        'interval_value',
        'interval_unit',
        'template',
        'is_active',
        'updated_at',
    )
    list_filter = ('interval_unit', 'is_active', 'template')
    search_fields = ('name', 'template__name')
    ordering = ('interval_value', 'name')
    readonly_fields = ('created_at', 'updated_at')
    actions = ('trigger_selected_followups_now',)

    @admin.action(description='Trigger selected follow-up schedules now')
    def trigger_selected_followups_now(self, request, queryset):
        from apps.messaging.services.followup_service import FollowUpSchedulerService

        stats = FollowUpSchedulerService().send_due_followups(
            schedule_ids=list(queryset.values_list('id', flat=True)),
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
