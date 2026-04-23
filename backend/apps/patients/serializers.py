from rest_framework import serializers
from .models import Patient
from apps.messaging.utils.phone import normalize_to_e164


class PatientSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    assigned_provider_name = serializers.SerializerMethodField()

    class Meta:
        model = Patient
        fields = [
            'id', 'first_name', 'last_name', 'middle_name', 'full_name',
            'date_of_birth', 'sex',
            'phone_number_raw', 'phone_number_e164',
            'condition', 'secondary_conditions', 'medications',
            'discharge_date', 'discharge_notes',
            'assigned_provider', 'assigned_provider_name', 'external_reference',
            'emergency_contact_name', 'emergency_contact_phone',
            'preferred_check_in_time', 'preferred_language', 'timezone',
            'sms_opt_in', 'consent_at', 'consent_source',
            'monitoring_active', 'follow_up_end_date',
            'current_risk_level', 'status',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'phone_number_e164', 'created_at', 'updated_at']

    def get_full_name(self, obj):
        return obj.get_full_name()

    def get_assigned_provider_name(self, obj):
        if obj.assigned_provider:
            return obj.assigned_provider.user.get_full_name()
        return None

    def validate_phone_number_raw(self, value):
        e164 = normalize_to_e164(value)
        if not e164:
            raise serializers.ValidationError('Invalid phone number. Please include country code.')
        return value

    def validate(self, attrs):
        phone_raw = attrs.get('phone_number_raw', getattr(self.instance, 'phone_number_raw', None))
        if phone_raw:
            e164 = normalize_to_e164(phone_raw)
            attrs['phone_number_e164'] = e164

            # Check uniqueness (excluding self on update)
            qs = Patient.objects.filter(phone_number_e164=e164)
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError(
                    {'phone_number_raw': 'A patient with this phone number already exists.'}
                )
        return attrs

    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['created_by'] = request.user
            # Auto-assign to provider's profile if provider
            if request.user.is_provider and not validated_data.get('assigned_provider'):
                try:
                    validated_data['assigned_provider'] = request.user.provider_profile
                except Exception:
                    pass
        return super().create(validated_data)


class PatientListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views."""
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = Patient
        fields = [
            'id', 'full_name', 'phone_number_e164',
            'condition', 'current_risk_level', 'status',
            'monitoring_active', 'discharge_date', 'assigned_provider',
        ]

    def get_full_name(self, obj):
        return obj.get_full_name()
