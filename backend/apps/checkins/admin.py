from django.contrib import admin
from .models import DailyCheckIn, CheckInResponse


class CheckInResponseInline(admin.TabularInline):
    """Inline admin for CheckInResponse."""
    model = CheckInResponse
    extra = 0
    readonly_fields = ('responded_at',)


@admin.register(DailyCheckIn)
class DailyCheckInAdmin(admin.ModelAdmin):
    """Admin interface for DailyCheckIn model."""
    
    list_display = (
        'patient', 'scheduled_date', 'scheduled_time', 'status',
        'risk_score', 'risk_level', 'completed_at'
    )
    list_filter = ('status', 'risk_level', 'scheduled_date')
    search_fields = ('patient__user__first_name', 'patient__user__last_name')
    ordering = ('-scheduled_date', '-scheduled_time')
    readonly_fields = ('created_at', 'sent_at', 'completed_at')
    inlines = [CheckInResponseInline]
    
    fieldsets = (
        ('Check-in Info', {
            'fields': ('patient', 'scheduled_date', 'scheduled_time', 'status')
        }),
        ('Risk Assessment', {
            'fields': ('risk_score', 'risk_level', 'notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'sent_at', 'completed_at')
        }),
    )
