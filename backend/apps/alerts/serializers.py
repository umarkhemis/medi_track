from rest_framework import serializers
from .models import Alert


class AlertSerializer(serializers.ModelSerializer):
    """Serializer for Alert model."""
    
    patient_name = serializers.CharField(source='patient.user.get_full_name', read_only=True)
    acknowledged_by_name = serializers.CharField(
        source='acknowledged_by.user.get_full_name',
        read_only=True
    )
    resolved_by_name = serializers.CharField(
        source='resolved_by.user.get_full_name',
        read_only=True
    )
    
    class Meta:
        model = Alert
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at', 'acknowledged_at', 'resolved_at')


class AlertListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for alert lists."""
    
    patient_name = serializers.CharField(source='patient.user.get_full_name', read_only=True)
    
    class Meta:
        model = Alert
        fields = (
            'id', 'patient', 'patient_name', 'alert_type',
            'status', 'risk_score', 'trigger_reason', 'created_at'
        )
