from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone

from .models import Alert
from .serializers import AlertSerializer, AlertListSerializer


class AlertViewSet(viewsets.ModelViewSet):
    """ViewSet for Alert model."""
    
    queryset = Alert.objects.select_related('patient__user', 'acknowledged_by__user').all()
    serializer_class = AlertSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['patient', 'alert_type', 'status']
    ordering_fields = ['created_at', 'risk_score']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return AlertListSerializer
        return AlertSerializer
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get active alerts only."""
        alerts = self.get_queryset().filter(status='active')
        serializer = self.get_serializer(alerts, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def acknowledge(self, request, pk=None):
        """Acknowledge an alert."""
        alert = self.get_object()
        
        if alert.status != 'active':
            return Response(
                {'error': 'Only active alerts can be acknowledged'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get provider from request.user if available
        provider = None
        if hasattr(request.user, 'provider_profile'):
            provider = request.user.provider_profile
        
        alert.status = 'acknowledged'
        alert.acknowledged_by = provider
        alert.acknowledged_at = timezone.now()
        alert.save()
        
        serializer = self.get_serializer(alert)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """Resolve an alert."""
        alert = self.get_object()
        
        if alert.status == 'resolved':
            return Response(
                {'error': 'Alert is already resolved'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get provider from request.user if available
        provider = None
        if hasattr(request.user, 'provider_profile'):
            provider = request.user.provider_profile
        
        alert.status = 'resolved'
        alert.resolved_by = provider
        alert.resolved_at = timezone.now()
        alert.resolution_notes = request.data.get('resolution_notes', '')
        alert.save()
        
        serializer = self.get_serializer(alert)
        return Response(serializer.data)
