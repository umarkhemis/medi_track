from django.contrib import admin
from .models import Provider


@admin.register(Provider)
class ProviderAdmin(admin.ModelAdmin):
    """Admin interface for Provider model."""
    
    list_display = (
        'user', 'employee_id', 'department', 'specialization',
        'is_available', 'current_patient_count', 'max_patients'
    )
    list_filter = ('department', 'is_available')
    search_fields = ('user__first_name', 'user__last_name', 'employee_id', 'license_number')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at', 'current_patient_count')
    
    fieldsets = (
        ('Provider Info', {
            'fields': ('user', 'employee_id', 'license_number')
        }),
        ('Department & Specialization', {
            'fields': ('department', 'specialization')
        }),
        ('Availability', {
            'fields': ('is_available', 'max_patients', 'current_patient_count')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
