from rest_framework import serializers
from .models import DailyCheckIn, CheckInResponse


class CheckInResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = CheckInResponse
        fields = ['id', 'question_key', 'response_value', 'raw_response_text', 'received_at']
        read_only_fields = ['id', 'received_at']


class DailyCheckInSerializer(serializers.ModelSerializer):
    responses = CheckInResponseSerializer(many=True, read_only=True)
    patient_name = serializers.SerializerMethodField()

    class Meta:
        model = DailyCheckIn
        fields = [
            'id', 'patient', 'patient_name', 'scheduled_date', 'scheduled_time',
            'status', 'question_keys', 'response_data',
            'sent_time', 'expiration_time', 'completed_time', 'missed_time',
            'attempt_count', 'reminder_count', 'last_attempt_time',
            'provider_message_id', 'correlation_id',
            'responses', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_patient_name(self, obj):
        return obj.patient.get_full_name()


class DailyCheckInListSerializer(serializers.ModelSerializer):
    patient_name = serializers.SerializerMethodField()

    class Meta:
        model = DailyCheckIn
        fields = ['id', 'patient', 'patient_name', 'scheduled_date', 'status', 'attempt_count', 'reminder_count']

    def get_patient_name(self, obj):
        return obj.patient.get_full_name()
