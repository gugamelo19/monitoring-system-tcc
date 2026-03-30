from rest_framework import serializers
from .models import Asset


class AssetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Asset
        fields = [
            "id",
            "name",
            "hostname",
            "ip_address",
            "mac_address",
            "asset_type",
            "location",
            "operating_system",
            "status",
            "is_monitored",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
