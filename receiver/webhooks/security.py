import hashlib
import hmac
import time

from django.conf import settings


TIMESTAMP_TOLERANCE_SECONDS = 300


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


def verify_signature(
    timestamp,
    event_id,
    raw_body,
    received_signature,
):
    expected_signature = generate_signature(
        timestamp=timestamp,
        event_id=event_id,
        raw_body=raw_body,
    )

    return hmac.compare_digest(
        expected_signature,
        received_signature,
    )


def is_timestamp_valid(timestamp):
    try:
        timestamp_int = int(timestamp)
    except (TypeError, ValueError):
        return False

    current_time = int(time.time())

    difference = abs(
        current_time - timestamp_int
    )

    return (
        difference
        <= TIMESTAMP_TOLERANCE_SECONDS
    )
