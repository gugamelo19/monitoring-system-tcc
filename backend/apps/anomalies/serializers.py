from rest_framework import serializers
from .models import Anomaly


class AnomalySerializer(serializers.ModelSerializer):
    asset_name = serializers.CharField(source="asset.name", read_only=True)

    class Meta:
        model = Anomaly
        fields = [
            "id",
            "event",
            "asset",
            "asset_name",
            "anomaly_type",
            "description",
            "severity",
            "score",
            "detection_rule",
            "status",
            "detected_at",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]
