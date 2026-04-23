from django.contrib import admin
from .models import DailyCheckIn, CheckInResponse


class CheckInResponseInline(admin.TabularInline):
    model = CheckInResponse
    extra = 0
    readonly_fields = ['received_at']


@admin.register(DailyCheckIn)
class DailyCheckInAdmin(admin.ModelAdmin):
    list_display = [
        'patient', 'scheduled_date', 'status',
        'attempt_count', 'reminder_count', 'sent_time', 'completed_time',
    ]
    list_filter = ['status', 'scheduled_date']
    search_fields = ['patient__first_name', 'patient__last_name', 'patient__phone_number_e164']
    readonly_fields = ['created_at', 'updated_at', 'sent_time', 'completed_time', 'missed_time']
    ordering = ['-scheduled_date']
    inlines = [CheckInResponseInline]


@admin.register(CheckInResponse)
class CheckInResponseAdmin(admin.ModelAdmin):
    list_display = ['patient', 'question_key', 'response_value', 'received_at']
    list_filter = ['question_key', 'response_value']
    search_fields = ['patient__first_name', 'patient__last_name']
    readonly_fields = ['received_at']
