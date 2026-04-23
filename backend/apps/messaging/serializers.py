from rest_framework import serializers
from .models import Message, MessageTemplate, FollowUpProgram, PatientProgramEnrollment, DeliveryReceipt


class MessageSerializer(serializers.ModelSerializer):
    patient_name = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = [
            'id', 'patient', 'patient_name', 'provider', 'channel',
            'direction', 'status', 'body', 'is_automated',
            'to_number', 'from_number', 'provider_message_id',
            'external_status', 'error_code', 'error_message',
            'checkin', 'sent_at', 'delivered_at', 'received_at',
            'failed_at', 'created_at',
        ]
        read_only_fields = [
            'id', 'direction', 'status', 'provider_message_id',
            'external_status', 'sent_at', 'delivered_at', 'received_at',
            'failed_at', 'created_at',
        ]

    def get_patient_name(self, obj):
        return obj.patient.get_full_name()


class SendMessageSerializer(serializers.Serializer):
    patient_id = serializers.IntegerField()
    body = serializers.CharField()


class MessageTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = MessageTemplate
        fields = '__all__'
        read_only_fields = ['id', 'created_at']


class FollowUpProgramSerializer(serializers.ModelSerializer):
    class Meta:
        model = FollowUpProgram
        fields = '__all__'
        read_only_fields = ['id', 'created_at']


class PatientProgramEnrollmentSerializer(serializers.ModelSerializer):
    program_name = serializers.CharField(source='program.name', read_only=True)
    patient_name = serializers.SerializerMethodField()

    class Meta:
        model = PatientProgramEnrollment
        fields = [
            'id', 'patient', 'patient_name', 'program', 'program_name',
            'enrolled_by', 'enrolled_at', 'end_date', 'is_active',
        ]
        read_only_fields = ['id', 'enrolled_at']

    def get_patient_name(self, obj):
        return obj.patient.get_full_name()
