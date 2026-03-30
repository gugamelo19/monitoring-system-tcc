from django.db.models import Count
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.assets.models import Asset
from apps.events.models import NetworkEvent
from apps.anomalies.models import Anomaly
from apps.alerts.models import Alert
from apps.events.serializers import NetworkEventSerializer
from apps.alerts.serializers import AlertSerializer


class DashboardSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        total_assets = Asset.objects.count()
        online_assets = Asset.objects.filter(
            status=Asset.AssetStatus.ONLINE).count()
        offline_assets = Asset.objects.filter(
            status=Asset.AssetStatus.OFFLINE).count()
        unstable_assets = Asset.objects.filter(
            status=Asset.AssetStatus.UNSTABLE).count()
        unknown_assets = Asset.objects.filter(
            status=Asset.AssetStatus.UNKNOWN).count()

        total_events = NetworkEvent.objects.count()
        total_anomalies = Anomaly.objects.count()

        open_alerts = Alert.objects.filter(status=Alert.Status.OPEN).count()
        in_progress_alerts = Alert.objects.filter(
            status=Alert.Status.IN_PROGRESS).count()
        resolved_alerts = Alert.objects.filter(
            status=Alert.Status.RESOLVED).count()
        false_positive_alerts = Alert.objects.filter(
            status=Alert.Status.FALSE_POSITIVE).count()

        data = {
            "assets": {
                "total": total_assets,
                "online": online_assets,
                "offline": offline_assets,
                "unstable": unstable_assets,
                "unknown": unknown_assets,
            },
            "events": {
                "total": total_events,
            },
            "anomalies": {
                "total": total_anomalies,
            },
            "alerts": {
                "open": open_alerts,
                "in_progress": in_progress_alerts,
                "resolved": resolved_alerts,
                "false_positive": false_positive_alerts,
            },
        }

        return Response(data)


class DashboardProtocolsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        protocol_counts = (
            NetworkEvent.objects.values("protocol")
            .annotate(total=Count("id"))
            .order_by("protocol")
        )

        data = [
            {
                "protocol": item["protocol"],
                "total": item["total"],
            }
            for item in protocol_counts
        ]

        return Response(data)


class DashboardSeverityView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        severity_counts = (
            Alert.objects.values("severity")
            .annotate(total=Count("id"))
            .order_by("severity")
        )

        data = [
            {
                "severity": item["severity"],
                "total": item["total"],
            }
            for item in severity_counts
        ]

        return Response(data)


class DashboardRecentEventsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        limit = int(request.query_params.get("limit", 10))
        events = NetworkEvent.objects.select_related("asset").all()[:limit]
        serializer = NetworkEventSerializer(events, many=True)
        return Response(serializer.data)


class DashboardRecentAlertsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        limit = int(request.query_params.get("limit", 10))
        alerts = Alert.objects.select_related(
            "anomaly", "anomaly__asset", "assigned_to").all()[:limit]
        serializer = AlertSerializer(alerts, many=True)
        return Response(serializer.data)


class DashboardAssetStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = {
            "online": Asset.objects.filter(status=Asset.AssetStatus.ONLINE).count(),
            "offline": Asset.objects.filter(status=Asset.AssetStatus.OFFLINE).count(),
            "unstable": Asset.objects.filter(status=Asset.AssetStatus.UNSTABLE).count(),
            "unknown": Asset.objects.filter(status=Asset.AssetStatus.UNKNOWN).count(),
        }
        return Response(data)


class DashboardAnomalyTypesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        anomaly_counts = (
            Anomaly.objects.values("anomaly_type")
            .annotate(total=Count("id"))
            .order_by("anomaly_type")
        )

        data = [
            {
                "anomaly_type": item["anomaly_type"],
                "total": item["total"],
            }
            for item in anomaly_counts
        ]

        return Response(data)
