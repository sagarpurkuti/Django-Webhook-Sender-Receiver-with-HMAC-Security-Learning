import json
import time

from django.http import JsonResponse

from .models import WebhookDelivery, WebhookEvent
from .security import generate_signature
from .services import deliver_webhook


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
        "version": "v1",
        "created_at": event.created_at.isoformat(),
        "source": "webhook-lab-sender",
        "data": event.payload,
    }

    raw_body = json.dumps(
        payload,
        separators=(",", ":"),
    ).encode()

    timestamp = str(
        int(time.time())
    )

    signature = generate_signature(
        timestamp=timestamp,
        event_id=str(event.event_id),
        raw_body=raw_body,
    )

    receiver_url = (
        "http://127.0.0.1:8001/webhooks/events/"
    )

    headers = {
        "Content-Type": "application/json",
        "X-Webhook-ID": str(event.event_id),
        "X-Webhook-Event": event.event_type,
        "X-Webhook-Version": "v1",
        "X-Webhook-Timestamp": timestamp,
        "X-Webhook-Signature": signature,
    }

    delivery = WebhookDelivery.objects.create(
        event=event,
        destination_url=receiver_url,
        payload=payload,
        request_headers=headers,
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

    print()
    print("======================================")
    print("         WEBHOOK SIGNATURE")
    print("======================================")
    print("Timestamp:")
    print(timestamp)

    print()
    print("Event ID:")
    print(event.event_id)

    print()
    print("Signature:")
    print(signature)

    print("======================================")

    response = deliver_webhook(delivery, raw_body)

    print()
    print("======================================")
    print("         WEBHOOK RESPONSE")
    print("======================================")

    print("Attempt:")
    print(delivery.attempt_number)

    print()
    print("Status:")
    print(delivery.status)

    if response is None:
        print()
        print("Error:")
        print(delivery.error_message)
        print("======================================")

        return JsonResponse(
            {
                "success": False,
                "event_id": str(event.event_id),
                "delivery_id": delivery.id,
                "attempt_number": delivery.attempt_number,
                "error": delivery.error_message,
            },
            status=502,
        )

    print()
    print("HTTP:")
    print(response.status_code)

    print()
    print("Duration:")
    print(f"{delivery.duration_ms:.2f} ms")

    print()
    print("Body:")
    print(response.text)

    print("======================================")

    try:
        receiver_response = response.json()
    except ValueError:
        receiver_response = response.text

    return JsonResponse(
        {
            "success": delivery.success,
            "event_id": str(event.event_id),
            "delivery_id": delivery.id,
            "attempt_number": delivery.attempt_number,
            "receiver_status": response.status_code,
            "receiver_response": receiver_response,
        }
    )
