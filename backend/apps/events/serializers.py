from rest_framework import serializers
from .models import NetworkEvent


class NetworkEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = NetworkEvent
        fields = [
            "id",
            "asset",
            "source_ip",
            "destination_ip",
            "source_port",
            "destination_port",
            "protocol",
            "transport_layer",
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
        read_only_fields = ["id", "created_at"]

    def validate(self, attrs):
        protocol = attrs.get("protocol")

        if protocol == "TCP" and attrs.get("destination_port") is None:
            raise serializers.ValidationError(
                {"destination_port": "destination_port é obrigatório para eventos TCP."}
            )

        if protocol == "DNS" and not attrs.get("dns_query"):
            raise serializers.ValidationError(
                {"dns_query": "dns_query é obrigatório para eventos DNS."}
            )

        return attrs
