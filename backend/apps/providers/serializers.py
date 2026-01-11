from rest_framework import serializers
from .models import Provider


class ProviderSerializer(serializers.ModelSerializer):
    """Serializer for Provider model."""
    
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    current_patient_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Provider
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at', 'current_patient_count')


class ProviderDashboardSerializer(serializers.Serializer):
    """Serializer for provider dashboard summary data."""
    
    total_patients = serializers.IntegerField()
    high_risk_patients = serializers.IntegerField()
    moderate_risk_patients = serializers.IntegerField()
    low_risk_patients = serializers.IntegerField()
    active_alerts = serializers.IntegerField()
    pending_checkins = serializers.IntegerField()
    checkin_response_rate = serializers.FloatField()
    pending_followups = serializers.IntegerField()
