import time

import requests

from django.utils import timezone

from .models import WebhookDelivery


RETRYABLE_STATUS_CODES = {
    429,
    500,
    502,
    503,
    504,
}


def should_retry(response):
    if response is None:
        return True

    return response.status_code in RETRYABLE_STATUS_CODES


def calculate_retry_delay(attempt_number):
    return 2 ** attempt_number


def deliver_webhook(delivery):
    delivery.status = "sending"
    delivery.sent_at = timezone.now()
    delivery.save(
        update_fields=[
            "status",
            "sent_at",
        ]
    )

    started_at = time.perf_counter()

    try:
        response = requests.post(
            delivery.destination_url,
            json=delivery.payload,
            headers=delivery.request_headers,
            timeout=10,
        )

        duration = time.perf_counter() - started_at

        delivery.response_status = response.status_code
        delivery.response_body = response.text
        delivery.duration_ms = duration * 1000
        delivery.completed_at = timezone.now()

        if 200 <= response.status_code < 300:
            delivery.success = True
            delivery.status = "success"

        else:
            delivery.success = False
            delivery.status = "failed"

        delivery.save()

        return response

    except requests.RequestException as exc:
        duration = time.perf_counter() - started_at

        delivery.success = False
        delivery.status = "failed"
        delivery.error_message = str(exc)
        delivery.duration_ms = duration * 1000
        delivery.completed_at = timezone.now()

        delivery.save()

        return None


def retry_delivery(delivery):
    new_delivery = WebhookDelivery.objects.create(
        event=delivery.event,
        destination_url=delivery.destination_url,
        payload=delivery.payload,
        request_headers=delivery.request_headers,
        attempt_number=delivery.attempt_number + 1,
    )

    deliver_webhook(new_delivery)

    return new_delivery
