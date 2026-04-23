from django.contrib import admin
from .models import (
    Message, DeliveryReceipt, InboundWebhookEvent,
    MessageTemplate, FollowUpProgram, PatientProgramEnrollment,
)


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['patient', 'direction', 'status', 'is_automated', 'channel', 'created_at']
    list_filter = ['direction', 'status', 'channel', 'is_automated']
    search_fields = ['patient__first_name', 'patient__last_name', 'patient__phone_number_e164', 'body']
    readonly_fields = ['created_at', 'sent_at', 'delivered_at', 'received_at', 'failed_at']
    ordering = ['-created_at']


@admin.register(DeliveryReceipt)
class DeliveryReceiptAdmin(admin.ModelAdmin):
    list_display = ['provider_message_id', 'status', 'received_at']
    list_filter = ['status']
    readonly_fields = ['received_at']


@admin.register(InboundWebhookEvent)
class InboundWebhookEventAdmin(admin.ModelAdmin):
    list_display = ['from_number', 'body', 'processed', 'received_at']
    list_filter = ['processed']
    search_fields = ['from_number', 'body']
    readonly_fields = ['received_at']


@admin.register(MessageTemplate)
class MessageTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'template_type', 'condition', 'language', 'is_active']
    list_filter = ['template_type', 'is_active', 'language']
    search_fields = ['name', 'condition', 'body']


@admin.register(FollowUpProgram)
class FollowUpProgramAdmin(admin.ModelAdmin):
    list_display = ['name', 'condition', 'duration_days', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'condition']


@admin.register(PatientProgramEnrollment)
class PatientProgramEnrollmentAdmin(admin.ModelAdmin):
    list_display = ['patient', 'program', 'enrolled_at', 'end_date', 'is_active']
    list_filter = ['is_active', 'program']
    search_fields = ['patient__first_name', 'patient__last_name']
    readonly_fields = ['enrolled_at']
