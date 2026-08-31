import time

import requests

from django.http import JsonResponse
from django.utils import timezone

from .models import WebhookDelivery, WebhookEvent


def send_webhook(request):
    event_type = request.GET.get(
        "type",
        "payment.completed",
    )

    event = WebhookEvent.objects.create(
        event_type=event_type,
        payload={
            "payment": {
                "payment_id": "pay_123",
                "amount": 1500,
                "currency": "NPR",
            }
        },
    )

    payload = {
        "id": str(event.event_id),
        "type": event.event_type,
        "created_at": event.created_at.isoformat(),
        "data": event.payload,
    }

    receiver_url = (
        "http://127.0.0.1:8001/webhooks/events/"
    )

    headers = {
        "X-Webhook-ID": str(event.event_id),
        "X-Webhook-Event": event.event_type,
    }

    delivery = WebhookDelivery.objects.create(
        event=event,
        destination_url=receiver_url,
        payload=payload,
        request_headers=headers,
        sent_at=timezone.now(),
    )

    print()
    print("======================================")
    print("         WEBHOOK EVENT CREATED")
    print("======================================")

    print("Event database ID:")
    print(event.id)

    print()
    print("Event ID:")
    print(event.event_id)

    print()
    print("Event Type:")
    print(event.event_type)

    print()
    print("Payload:")
    print(payload)

    print()
    print("Delivery ID:")
    print(delivery.id)

    print("======================================")

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
        print("======================================")
        print("         WEBHOOK RESPONSE")
        print("======================================")

        print("Status:")
        print(response.status_code)

        print()
        print("Duration:")
        print(f"{duration * 1000:.2f} ms")

        print()
        print("Body:")
        print(response.text)

        print("======================================")

        return JsonResponse(
            {
                "success": delivery.success,
                "event_id": str(event.event_id),
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

        return JsonResponse(
            {
                "success": False,
                "event_id": str(event.event_id),
                "delivery_id": delivery.id,
                "error": str(exc),
            },
            status=502,
        )
