from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import Anomaly
from .serializers import AnomalySerializer


class AnomalyViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Anomaly.objects.select_related("asset", "event").all()
    serializer_class = AnomalySerializer
    permission_classes = [IsAuthenticated]
