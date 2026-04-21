from django.contrib import admin
from .models import MessageTemplate, Message


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
        'is_automated', 'created_at', 'sent_at'
    )
    list_filter = ('channel', 'direction', 'status', 'is_automated', 'created_at')
    search_fields = ('patient__user__first_name', 'patient__user__last_name', 'content')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'sent_at', 'delivered_at', 'read_at', 'message_sid')
