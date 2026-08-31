import json

from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from .models import WebhookEvent


@csrf_exempt
def receive_webhook(request):
    print()
    print("======================================")
    print("         WEBHOOK RECEIVED")
    print("======================================")

    print("Method:", request.method)
    print("Path:", request.path)

    print()
    print("Headers:")
    print(request.headers)

    print()
    print("Raw Body:")
    print(request.body)

    print("======================================")

    if request.method != "POST":
        return JsonResponse(
            {
                "success": False,
                "message": "Only POST requests are allowed.",
            },
            status=405,
        )

    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse(
            {
                "success": False,
                "message": "Invalid JSON.",
            },
            status=400,
        )

    event_id = payload.get("id")
    event_type = payload.get("type")

    if not event_id:
        return JsonResponse(
            {
                "success": False,
                "message": "event_id is required.",
            },
            status=400,
        )

    if not event_type:
        return JsonResponse(
            {
                "success": False,
                "message": "event_type is required.",
            },
            status=400,
        )

    print()
    print("Parsed JSON:")
    print(payload)

    event = WebhookEvent.objects.create(
        event_id=event_id,
        event_type=event_type,
        payload=payload,
        status="received",
    )

    print()
    print("Database record created:")
    print(event.id)

    event.status = "processed"
    event.processed_at = timezone.now()
    event.save(
        update_fields=[
            "status",
            "processed_at",
        ]
    )

    return JsonResponse(
        {
            "success": True,
            "message": "Webhook received successfully.",
            "event_id": event.event_id,
            "event_type": event.event_type,
        },
        status=200,
    )
