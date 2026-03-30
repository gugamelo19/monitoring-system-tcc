from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import NetworkEvent
from .serializers import NetworkEventSerializer
from apps.anomalies.services.detector import AnomalyDetectorService


class NetworkEventViewSet(viewsets.ModelViewSet):
    queryset = NetworkEvent.objects.select_related("asset").all()
    serializer_class = NetworkEventSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post", "head", "options"]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        event = serializer.save()

        AnomalyDetectorService.analyze_event(event)

        response_data = {
            "message": "Evento registrado com sucesso.",
            "event": NetworkEventSerializer(event).data,
        }

        return Response(response_data, status=status.HTTP_201_CREATED)
