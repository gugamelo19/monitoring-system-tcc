from rest_framework import serializers

from .models import NetworkEvent


class NetworkEventSerializer(serializers.ModelSerializer):
    asset_name = serializers.CharField(source="asset.name", read_only=True)

    class Meta:
        model = NetworkEvent
        fields = [
            "id",
            "asset",
            "asset_name",
            "protocol",
            "source_ip",
            "destination_ip",
            "source_port",
            "destination_port",
            "packet_size",
            "tcp_flags",
            "dns_query",
            "icmp_type",
            "icmp_code",
            "event_timestamp",
            "raw_summary",
            "collector_name",
            "created_at",
        ]
