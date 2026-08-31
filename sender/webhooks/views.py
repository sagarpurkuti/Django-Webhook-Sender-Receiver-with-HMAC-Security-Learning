import time

import requests

from django.http import JsonResponse
from django.utils import timezone

from .models import WebhookDelivery


def send_webhook(request):
    payload = {
        "event_id": "evt_001",
        "event_type": "payment.completed",
        "data": {
            "payment_id": "pay_123",
            "amount": 1500,
            "currency": "NPR",
        },
    }

    receiver_url = (
        "http://127.0.0.1:8001/webhooks/events/"
    )

    headers = {
        "X-Webhook-Event": payload["event_type"],
        "X-Webhook-ID": payload["event_id"],
    }

    delivery = WebhookDelivery.objects.create(
        event_id=payload["event_id"],
        event_type=payload["event_type"],
        destination_url=receiver_url,
        payload=payload,
        request_headers=headers,
        sent_at=timezone.now(),
    )

    print()
    print("======================================")
    print("         SENDING WEBHOOK")
    print("======================================")

    print("Delivery ID:")
    print(delivery.id)

    print()
    print("Destination:")
    print(receiver_url)

    print()
    print("Headers:")
    print(headers)

    print()
    print("Payload:")
    print(payload)

    try:
        started_at = time.perf_counter()

        response = requests.post(
            receiver_url,
            json=payload,
            headers=headers,
            timeout=10,
        )

        duration = time.perf_counter() - started_at

        delivery.response_status = response.status_code
        delivery.response_body = response.text
        delivery.completed_at = timezone.now()
        delivery.duration_ms = duration * 1000
        delivery.success = (
            200 <= response.status_code < 300
        )

        delivery.save()

        print()
        print("Response Status:")
        print(response.status_code)

        print()
        print("Response Body:")
        print(response.text)

        print()
        print("Duration:")
        print(f"{duration:.4f} seconds")

        print("======================================")
        print()

        return JsonResponse(
            {
                "success": delivery.success,
                "delivery_id": delivery.id,
                "receiver_status": response.status_code,
                "receiver_response": response.json(),
            }
        )

    except requests.RequestException as exc:
        delivery.completed_at = timezone.now()
        delivery.error_message = str(exc)
        delivery.success = False

        delivery.save()

        print()
        print("Webhook delivery failed:")
        print(exc)

        print("======================================")
        print()

        return JsonResponse(
            {
                "success": False,
                "delivery_id": delivery.id,
                "error": str(exc),
            },
            status=502,
        )
