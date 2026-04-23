from django.contrib import admin
from .models import Provider


@admin.register(Provider)
class ProviderAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'facility_name', 'department', 'specialization', 'is_active', 'is_available', 'patient_count']
    list_filter = ['is_active', 'is_available', 'facility_name']
    search_fields = ['user__first_name', 'user__last_name', 'user__email', 'facility_name', 'department']
    readonly_fields = ['created_at', 'updated_at']

    def full_name(self, obj):
        return obj.user.get_full_name()
    full_name.short_description = 'Name'

    def patient_count(self, obj):
        return obj.patient_count
    patient_count.short_description = 'Active Patients'
