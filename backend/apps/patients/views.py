from rest_framework import generics, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from django.db.models import Q
from .models import Patient
from .serializers import PatientSerializer, PatientListSerializer
from .permissions import IsProviderOrAdmin, CanAccessPatient
from apps.messaging.models import FollowUpProgram, PatientProgramEnrollment
from rest_framework import serializers as drf_serializers


class PatientViewSet(ModelViewSet):
    permission_classes = [IsProviderOrAdmin]

    def get_serializer_class(self):
        if self.action == 'list':
            return PatientListSerializer
        return PatientSerializer

    def get_queryset(self):
        user = self.request.user
        qs = Patient.objects.select_related('assigned_provider__user')

        if user.role == 'admin':
            pass  # all patients
        elif user.role == 'provider':
            try:
                qs = qs.filter(assigned_provider=user.provider_profile)
            except Exception:
                qs = qs.none()

        # Filters
        risk = self.request.query_params.get('risk_level')
        status_filter = self.request.query_params.get('status')
        search = self.request.query_params.get('search')

        if risk:
            qs = qs.filter(current_risk_level=risk)
        if status_filter:
            qs = qs.filter(status=status_filter)
        if search:
            qs = qs.filter(
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(phone_number_e164__icontains=search) |
                Q(condition__icontains=search)
            )
        return qs

    def get_object(self):
        obj = super().get_object()
        self.check_object_permissions(self.request, obj)
        return obj

    def check_object_permissions(self, request, obj):
        super().check_object_permissions(request, obj)
        perm = CanAccessPatient()
        if not perm.has_object_permission(request, self, obj):
            self.permission_denied(request)

    @action(detail=False, methods=['get'])
    def high_risk(self, request):
        qs = self.get_queryset().filter(current_risk_level=Patient.RiskLevel.RED)
        serializer = PatientListSerializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def pause_monitoring(self, request, pk=None):
        patient = self.get_object()
        patient.pause_monitoring()
        return Response({'status': 'monitoring paused'})

    @action(detail=True, methods=['post'])
    def resume_monitoring(self, request, pk=None):
        patient = self.get_object()
        patient.resume_monitoring()
        return Response({'status': 'monitoring resumed'})

    @action(detail=True, methods=['post'])
    def opt_out(self, request, pk=None):
        patient = self.get_object()
        patient.opt_out()
        return Response({'status': 'patient opted out'})

    @action(detail=True, methods=['post'])
    def mark_unreachable(self, request, pk=None):
        patient = self.get_object()
        patient.mark_unreachable()
        return Response({'status': 'patient marked unreachable'})

    @action(detail=True, methods=['post'])
    def enroll(self, request, pk=None):
        patient = self.get_object()
        program_id = request.data.get('program_id')
        if not program_id:
            return Response({'error': 'program_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            program = FollowUpProgram.objects.get(pk=program_id)
        except FollowUpProgram.DoesNotExist:
            return Response({'error': 'Program not found'}, status=status.HTTP_404_NOT_FOUND)

        # Deactivate previous enrollment
        PatientProgramEnrollment.objects.filter(patient=patient, is_active=True).update(is_active=False)

        import datetime
        end_date = (
            datetime.date.today() + datetime.timedelta(days=program.duration_days)
            if program.duration_days else None
        )
        enrollment = PatientProgramEnrollment.objects.create(
            patient=patient,
            program=program,
            enrolled_by=request.user,
            end_date=end_date,
        )
        if end_date:
            patient.follow_up_end_date = end_date
            patient.save(update_fields=['follow_up_end_date'])

        return Response({
            'status': 'enrolled',
            'program': program.name,
            'end_date': end_date,
        }, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'])
    def checkins(self, request, pk=None):
        patient = self.get_object()
        from apps.checkins.models import DailyCheckIn
        from apps.checkins.serializers import DailyCheckInSerializer
        qs = DailyCheckIn.objects.filter(patient=patient).order_by('-scheduled_date')
        serializer = DailyCheckInSerializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def alerts(self, request, pk=None):
        patient = self.get_object()
        from apps.alerts.models import Alert
        from apps.alerts.serializers import AlertSerializer
        qs = Alert.objects.filter(patient=patient).order_by('-created_at')
        serializer = AlertSerializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def messages(self, request, pk=None):
        patient = self.get_object()
        from apps.messaging.models import Message
        from apps.messaging.serializers import MessageSerializer
        qs = Message.objects.filter(patient=patient).order_by('-created_at')
        serializer = MessageSerializer(qs, many=True)
        return Response(serializer.data)
