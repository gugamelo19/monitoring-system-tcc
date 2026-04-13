from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from apps.anomalies.services.detector import AnomalyDetectorService
from .models import NetworkEvent
from .serializers import NetworkEventSerializer


class NetworkEventViewSet(viewsets.ModelViewSet):
    queryset = NetworkEvent.objects.select_related(
        "asset").all().order_by("-event_timestamp")
    serializer_class = NetworkEventSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        event = serializer.save()
        AnomalyDetectorService.analyze_event(event)
