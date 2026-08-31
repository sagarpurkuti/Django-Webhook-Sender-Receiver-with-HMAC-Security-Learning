from django.contrib import admin

from .models import WebhookEvent


@admin.register(WebhookEvent)
class WebhookEventAdmin(admin.ModelAdmin):
    list_display = (
        "event_id",
        "event_type",
        "status",
        "received_at",
        "processed_at",
    )

    list_filter = (
        "status",
        "event_type",
    )

    search_fields = (
        "event_id",
        "event_type",
    )
