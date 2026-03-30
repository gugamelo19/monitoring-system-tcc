from rest_framework import serializers
from .models import Alert


class AlertSerializer(serializers.ModelSerializer):
    anomaly_type = serializers.CharField(
        source="anomaly.anomaly_type", read_only=True)
    asset_name = serializers.CharField(
        source="anomaly.asset.name", read_only=True)

    class Meta:
        model = Alert
        fields = [
            "id",
            "anomaly",
            "anomaly_type",
            "asset_name",
            "title",
            "message",
            "severity",
            "status",
            "assigned_to",
            "created_at",
            "updated_at",
            "resolved_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "resolved_at"]
