from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone

from .models import DailyCheckIn, CheckInResponse
from .serializers import (
    DailyCheckInSerializer,
    DailyCheckInListSerializer,
    CheckInResponseSerializer
)


class DailyCheckInViewSet(viewsets.ModelViewSet):
    """ViewSet for DailyCheckIn model."""
    
    queryset = DailyCheckIn.objects.select_related('patient__user').prefetch_related('responses').all()
    serializer_class = DailyCheckInSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['patient', 'status', 'risk_level', 'scheduled_date']
    ordering_fields = ['scheduled_date', 'risk_score']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return DailyCheckInListSerializer
        return DailyCheckInSerializer
    
    @action(detail=False, methods=['get'])
    def today(self, request):
        """Get today's check-ins."""
        today = timezone.now().date()
        checkins = self.get_queryset().filter(scheduled_date=today)
        serializer = self.get_serializer(checkins, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def send(self, request, pk=None):
        """Manually trigger check-in message."""
        # This would integrate with the messaging service
        checkin = self.get_object()
        
        if checkin.status != 'scheduled':
            return Response(
                {'error': 'Check-in has already been sent or completed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # TODO: Integrate with CheckInScheduler service
        checkin.status = 'sent'
        checkin.sent_at = timezone.now()
        checkin.save()
        
        return Response({'message': 'Check-in sent successfully'})
    
    @action(detail=True, methods=['get'])
    def responses(self, request, pk=None):
        """Get check-in responses."""
        checkin = self.get_object()
        responses = checkin.responses.all()
        serializer = CheckInResponseSerializer(responses, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def schedule(self, request):
        """Schedule check-ins for all active patients."""
        # TODO: Integrate with CheckInScheduler service
        return Response({'message': 'Check-ins scheduled successfully'})
