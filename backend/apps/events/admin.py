from django.contrib import admin
from .models import NetworkEvent


@admin.register(NetworkEvent)
class NetworkEventAdmin(admin.ModelAdmin):
    list_display = ("protocol", "source_ip", "destination_ip",
                    "destination_port", "event_timestamp")
    search_fields = ("source_ip", "destination_ip", "dns_query")
    list_filter = ("protocol", "collector_name")
