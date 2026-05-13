from django.contrib import admin
from .models import Anomaly, FalsePositiveFeedback, TrustedSource


@admin.register(Anomaly)
class AnomalyAdmin(admin.ModelAdmin):
    list_display = ("anomaly_type", "severity",
                    "status", "asset", "detected_at")
    search_fields = ("anomaly_type", "description", "detection_rule")
    list_filter = ("severity", "status")


@admin.register(TrustedSource)
class TrustedSourceAdmin(admin.ModelAdmin):
    list_display = ("ip_address", "description", "is_active",
                    "created_at", "updated_at")
    search_fields = ("ip_address", "description")
    list_filter = ("is_active",)
    list_editable = ("is_active",)


@admin.register(FalsePositiveFeedback)
class FalsePositiveFeedbackAdmin(admin.ModelAdmin):
    list_display = ("source_ip", "anomaly_type",
                    "suppress_until", "created_at")
    search_fields = ("source_ip", "anomaly_type", "note")
    list_filter = ("anomaly_type",)
