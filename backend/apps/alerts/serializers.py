from rest_framework import serializers
from .models import Alert, EscalationTask


class EscalationTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = EscalationTask
        fields = [
            'id', 'alert', 'patient', 'assigned_to', 'status',
            'instructions', 'action_taken', 'due_by', 'completed_at', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class AlertSerializer(serializers.ModelSerializer):
    patient_name = serializers.SerializerMethodField()
    alert_type = serializers.CharField(source='severity', read_only=True)
    trigger_reason = serializers.CharField(source='description', read_only=True)
    escalation_tasks = EscalationTaskSerializer(many=True, read_only=True)

    class Meta:
        model = Alert
        fields = [
            'id', 'patient', 'patient_name', 'checkin', 'severity', 'alert_type',
            'status', 'title', 'description', 'trigger_reason', 'triggered_by',
            'assigned_to', 'acknowledged_by', 'acknowledged_at',
            'resolved_by', 'resolved_at', 'resolution_notes',
            'escalation_tasks', 'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'severity', 'alert_type', 'trigger_reason', 'triggered_by',
            'acknowledged_at', 'resolved_at', 'created_at', 'updated_at',
        ]

    def get_patient_name(self, obj):
        return obj.patient.get_full_name()
