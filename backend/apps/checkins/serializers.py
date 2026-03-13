from rest_framework import serializers
from .models import DailyCheckIn, CheckInResponse


class CheckInResponseSerializer(serializers.ModelSerializer):
    """Serializer for CheckInResponse model."""
    
    class Meta:
        model = CheckInResponse
        fields = '__all__'
        read_only_fields = ('responded_at',)


class DailyCheckInSerializer(serializers.ModelSerializer):
    """Serializer for DailyCheckIn model."""
    
    patient_name = serializers.CharField(source='patient.user.get_full_name', read_only=True)
    responses = CheckInResponseSerializer(many=True, read_only=True)
    
    class Meta:
        model = DailyCheckIn
        fields = '__all__'
        read_only_fields = ('created_at', 'sent_at', 'completed_at')


class DailyCheckInListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for check-in lists."""
    
    patient_name = serializers.CharField(source='patient.user.get_full_name', read_only=True)
    
    class Meta:
        model = DailyCheckIn
        fields = (
            'id', 'patient', 'patient_name', 'scheduled_date',
            'scheduled_time', 'status', 'risk_score', 'risk_level'
        )
