import uuid

from django.db import models


class WebhookEvent(models.Model):
    event_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
    )

    event_type = models.CharField(
        max_length=255,
    )

    payload = models.JSONField()

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    def __str__(self):
        return f"{self.event_id} - {self.event_type}"


class WebhookDelivery(models.Model):
    event = models.ForeignKey(
        WebhookEvent,
        on_delete=models.CASCADE,
        related_name="deliveries",
    )

    destination_url = models.URLField()

    payload = models.JSONField()

    request_headers = models.JSONField(
        default=dict,
    )

    sent_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    completed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    duration_ms = models.FloatField(
        null=True,
        blank=True,
    )

    response_status = models.PositiveIntegerField(
        null=True,
        blank=True,
    )

    response_body = models.TextField(
        blank=True,
        null=True,
    )

    success = models.BooleanField(
        default=False,
    )

    error_message = models.TextField(
        blank=True,
        null=True,
    )

    def __str__(self):
        return f"{self.event.event_id} - {self.event.event_type}"
