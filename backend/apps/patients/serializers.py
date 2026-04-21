from rest_framework import serializers
from .models import Patient


class PatientSerializer(serializers.ModelSerializer):
    """Serializer for Patient model."""
    
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    provider_name = serializers.CharField(
        source='assigned_provider.user.get_full_name',
        read_only=True,
        allow_null=True,
    )
    days_since_discharge = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Patient
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at', 'current_risk_level')


class PatientListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for patient lists."""
    
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    provider_name = serializers.CharField(
        source='assigned_provider.user.get_full_name',
        read_only=True,
        allow_null=True,
    )
    days_since_discharge = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Patient
        fields = (
            'id', 'user_name', 'condition', 'current_risk_level',
            'discharge_date', 'days_since_discharge', 'provider_name',
            'monitoring_active', 'follow_up_date'
        )
