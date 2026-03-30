from django.contrib import admin
from .models import Anomaly


@admin.register(Anomaly)
class AnomalyAdmin(admin.ModelAdmin):
    list_display = ("anomaly_type", "severity",
                    "status", "asset", "detected_at")
    search_fields = ("anomaly_type", "description", "detection_rule")
    list_filter = ("severity", "status")
