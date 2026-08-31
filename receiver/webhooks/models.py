from django.db import models


class WebhookEvent(models.Model):
    event_id = models.CharField(max_length=255, unique=True)
    event_type = models.CharField(max_length=255)

    payload = models.JSONField()

    received_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    status = models.CharField(
        max_length=50,
        default="received",
    )

    error_message = models.TextField(
        blank=True,
        null=True,
    )

    def __str__(self):
        return f"{self.event_id} - {self.event_type}"
