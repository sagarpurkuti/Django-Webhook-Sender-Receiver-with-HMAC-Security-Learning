from django.contrib import admin

from .models import WebhookDelivery


@admin.register(WebhookDelivery)
class WebhookDeliveryAdmin(admin.ModelAdmin):
    list_display = (
        "event_id",
        "event_type",
        "response_status",
        "success",
        "duration_ms",
        "sent_at",
        "completed_at",
    )

    list_filter = (
        "success",
        "event_type",
        "response_status",
    )

    search_fields = (
        "event_id",
        "event_type",
        "destination_url",
    )
