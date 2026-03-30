from django.contrib import admin
from .models import Asset


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = ("name", "ip_address", "asset_type",
                    "status", "is_monitored")
    search_fields = ("name", "hostname", "ip_address")
    list_filter = ("asset_type", "status", "is_monitored")
