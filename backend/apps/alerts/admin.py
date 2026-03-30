from django.contrib import admin
from .models import Alert


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ("title", "severity", "status", "assigned_to", "created_at")
    search_fields = ("title", "message")
    list_filter = ("severity", "status")
