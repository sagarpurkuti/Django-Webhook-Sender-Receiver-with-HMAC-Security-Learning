import hashlib
import hmac

from django.conf import settings


def generate_signature(
    timestamp,
    event_id,
    raw_body,
):
    message = (
        f"{timestamp}.{event_id}."
    ).encode() + raw_body

    signature = hmac.new(
        settings.WEBHOOK_SECRET.encode(),
        message,
        hashlib.sha256,
    ).hexdigest()

    return f"sha256={signature}"
