from django.contrib import admin

from .models import WebhookDelivery, WebhookEvent


@admin.register(WebhookEvent)
class WebhookEventAdmin(admin.ModelAdmin):
    list_display = (
        "event_id",
        "event_type",
        "delivery_count",
        "created_at",
    )

    list_filter = (
        "event_type",
    )

    search_fields = (
        "event_id",
        "event_type",
    )

    def delivery_count(self, obj):
        return obj.deliveries.count()

    delivery_count.short_description = "Deliveries"


@admin.register(WebhookDelivery)
class WebhookDeliveryAdmin(admin.ModelAdmin):
    list_display = (
        "event",
        "response_status",
        "success",
        "duration_ms",
        "sent_at",
        "completed_at",
    )

    list_filter = (
        "success",
        "response_status",
    )

    search_fields = (
        "event__event_id",
        "event__event_type",
        "destination_url",
    )
