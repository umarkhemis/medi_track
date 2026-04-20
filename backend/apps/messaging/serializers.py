from rest_framework import serializers
from .models import MessageTemplate, Message


class MessageTemplateSerializer(serializers.ModelSerializer):
    """Serializer for MessageTemplate model."""
    
    class Meta:
        model = MessageTemplate
        fields = '__all__'
        read_only_fields = ('created_at',)


class MessageSerializer(serializers.ModelSerializer):
    """Serializer for Message model."""
    
    patient_name = serializers.CharField(source='patient.user.get_full_name', read_only=True)
    provider_name = serializers.CharField(source='provider.user.get_full_name', read_only=True)
    
    class Meta:
        model = Message
        fields = '__all__'
        read_only_fields = (
            'created_at', 'sent_at', 'delivered_at', 'read_at', 'message_sid'
        )
