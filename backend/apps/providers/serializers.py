from rest_framework import serializers
from .models import Provider
from apps.users.serializers import UserProfileSerializer


class ProviderSerializer(serializers.ModelSerializer):
    user = UserProfileSerializer(read_only=True)
    patient_count = serializers.IntegerField(read_only=True)
    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = Provider
        fields = [
            'id', 'user', 'full_name', 'specialization', 'facility_name',
            'department', 'timezone', 'is_active', 'is_available',
            'max_patients', 'patient_count', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class ProviderDashboardSerializer(serializers.Serializer):
    total_patients = serializers.IntegerField()
    active_patients = serializers.IntegerField()
    high_risk_patients = serializers.IntegerField()
    yellow_risk_patients = serializers.IntegerField()
    pending_alerts = serializers.IntegerField()
    todays_checkins = serializers.IntegerField()
    completed_checkins_today = serializers.IntegerField()
    missed_checkins_today = serializers.IntegerField()
