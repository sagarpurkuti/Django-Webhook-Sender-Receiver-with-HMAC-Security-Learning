import json
import uuid

from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from .models import WebhookEvent


SUPPORTED_EVENT_TYPES = {
    "payment.created",
    "payment.completed",
    "payment.failed",
}

SUPPORTED_VERSIONS = {
    "v1",
}

EXPECTED_SOURCE = "webhook-lab-sender"


@csrf_exempt
def receive_webhook(request):
    print()
    print("======================================")
    print("         WEBHOOK RECEIVED")
    print("======================================")

    print("Method:")
    print(request.method)

    print()
    print("Path:")
    print(request.path)

    print()
    print("Headers:")

    for key, value in request.headers.items():
        print(f"{key}: {value}")

    print()
    print("Raw Body:")
    print(request.body)

    print("======================================")

    # -------------------------------------------------
    # 1. Validate HTTP method
    # -------------------------------------------------

    if request.method != "POST":
        return JsonResponse(
            {
                "success": False,
                "error": {
                    "code": "method_not_allowed",
                    "message": "Only POST requests are allowed.",
                },
            },
            status=405,
        )

    # -------------------------------------------------
    # 2. Validate Content-Type
    # -------------------------------------------------

    content_type = request.headers.get(
        "Content-Type",
        ""
    )

    if not content_type.startswith("application/json"):
        return JsonResponse(
            {
                "success": False,
                "error": {
                    "code": "invalid_content_type",
                    "message": "Content-Type must be application/json.",
                },
            },
            status=415,
        )

    # -------------------------------------------------
    # 3. Parse JSON
    # -------------------------------------------------

    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse(
            {
                "success": False,
                "error": {
                    "code": "invalid_json",
                    "message": "Request body contains invalid JSON.",
                },
            },
            status=400,
        )

    # -------------------------------------------------
    # 4. Validate payload is an object
    # -------------------------------------------------

    if not isinstance(payload, dict):
        return JsonResponse(
            {
                "success": False,
                "error": {
                    "code": "invalid_payload",
                    "message": "Webhook payload must be a JSON object.",
                },
            },
            status=400,
        )

    # -------------------------------------------------
    # 5. Extract fields
    # -------------------------------------------------

    event_id = payload.get("id")
    event_type = payload.get("type")
    version = payload.get("version")
    created_at = payload.get("created_at")
    source = payload.get("source")
    data = payload.get("data")

    # -------------------------------------------------
    # 6. Required fields
    # -------------------------------------------------

    required_fields = {
        "id": event_id,
        "type": event_type,
        "version": version,
        "created_at": created_at,
        "source": source,
        "data": data,
    }

    missing_fields = [
        field
        for field, value in required_fields.items()
        if value is None
    ]

    if missing_fields:
        return JsonResponse(
            {
                "success": False,
                "error": {
                    "code": "missing_fields",
                    "message": "Required webhook fields are missing.",
                    "fields": missing_fields,
                },
            },
            status=400,
        )

    # -------------------------------------------------
    # 7. Validate UUID
    # -------------------------------------------------

    try:
        uuid.UUID(str(event_id))
    except (ValueError, TypeError, AttributeError):
        return JsonResponse(
            {
                "success": False,
                "error": {
                    "code": "invalid_event_id",
                    "message": "Webhook id must be a valid UUID.",
                },
            },
            status=400,
        )

    # -------------------------------------------------
    # 8. Validate event type
    # -------------------------------------------------

    if event_type not in SUPPORTED_EVENT_TYPES:
        return JsonResponse(
            {
                "success": False,
                "error": {
                    "code": "unsupported_event_type",
                    "message": f"Unsupported event type: {event_type}",
                },
            },
            status=400,
        )

    # -------------------------------------------------
    # 9. Validate version
    # -------------------------------------------------

    if version not in SUPPORTED_VERSIONS:
        return JsonResponse(
            {
                "success": False,
                "error": {
                    "code": "unsupported_version",
                    "message": f"Unsupported webhook version: {version}",
                },
            },
            status=400,
        )

    # -------------------------------------------------
    # 10. Validate source
    # -------------------------------------------------

    if source != EXPECTED_SOURCE:
        return JsonResponse(
            {
                "success": False,
                "error": {
                    "code": "invalid_source",
                    "message": "Unknown webhook source.",
                },
            },
            status=400,
        )

    # -------------------------------------------------
    # 11. Validate data
    # -------------------------------------------------

    if not isinstance(data, dict):
        return JsonResponse(
            {
                "success": False,
                "error": {
                    "code": "invalid_data",
                    "message": "Webhook data must be a JSON object.",
                },
            },
            status=400,
        )

    # -------------------------------------------------
    # 12. Validate headers
    # -------------------------------------------------

    header_event_id = request.headers.get(
        "X-Webhook-ID"
    )

    header_event_type = request.headers.get(
        "X-Webhook-Event"
    )

    header_version = request.headers.get(
        "X-Webhook-Version"
    )

    if header_event_id != str(event_id):
        return JsonResponse(
            {
                "success": False,
                "error": {
                    "code": "event_id_mismatch",
                    "message": "X-Webhook-ID does not match payload id.",
                },
            },
            status=400,
        )

    if header_event_type != event_type:
        return JsonResponse(
            {
                "success": False,
                "error": {
                    "code": "event_type_mismatch",
                    "message": "X-Webhook-Event does not match payload type.",
                },
            },
            status=400,
        )

    if header_version != version:
        return JsonResponse(
            {
                "success": False,
                "error": {
                    "code": "version_mismatch",
                    "message": "X-Webhook-Version does not match payload version.",
                },
            },
            status=400,
        )

    print()
    print("Webhook validation:")
    print("PASSED")

    # -------------------------------------------------
    # 13. Save event
    # -------------------------------------------------

    event = WebhookEvent.objects.create(
        event_id=str(event_id),
        event_type=event_type,
        payload=payload,
        status="received",
    )

    print()
    print("Event saved:")
    print(event.id)

    # -------------------------------------------------
    # 14. Process event
    # -------------------------------------------------

    print()
    print("Processing event:")
    print(event_type)

    event.status = "processed"
    event.processed_at = timezone.now()

    event.save(
        update_fields=[
            "status",
            "processed_at",
        ]
    )

    print()
    print("Event processing:")
    print("SUCCESS")

    print("======================================")
    print()

    return JsonResponse(
        {
            "success": True,
            "message": "Webhook received and processed successfully.",
            "event": {
                "id": str(event.event_id),
                "type": event.event_type,
                "version": version,
            },
        },
        status=200,
    )
