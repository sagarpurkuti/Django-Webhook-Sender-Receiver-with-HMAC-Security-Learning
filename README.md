# Django Webhook Lab

A hands-on learning project that demonstrates how to build, send, receive, and secure webhooks using two separate Django applications. The repository is designed for engineers and technical managers who want a concrete reference for production-style webhook architecture — not just a single HTTP endpoint that accepts JSON.

---

## Table of Contents

- [Executive Summary](#executive-summary)
- [What This Project Demonstrates](#what-this-project-demonstrates)
- [Architecture Overview](#architecture-overview)
- [Repository Structure](#repository-structure)
- [Prerequisites](#prerequisites)
- [Getting Started](#getting-started)
- [Environment Variables and Secrets](#environment-variables-and-secrets)
- [Running the Applications](#running-the-applications)
- [End-to-End Webhook Flow](#end-to-end-webhook-flow)
- [Webhook Event Contract](#webhook-event-contract)
- [HTTP Headers](#http-headers)
- [Security Model](#security-model)
- [Database Models](#database-models)
- [API Endpoints](#api-endpoints)
- [Django Admin](#django-admin)
- [Testing Guide](#testing-guide)
- [Troubleshooting](#troubleshooting)
- [Implementation Stages](#implementation-stages)
- [Production Considerations](#production-considerations)
- [Tech Stack](#tech-stack)

---

## Executive Summary

This repository contains **two independent Django 6.1 projects** that communicate over HTTP:

| Application | Port | Role |
|---|---|---|
| **Sender** | `8000` | Creates webhook events, signs them with HMAC, delivers them, and records delivery history |
| **Receiver** | `8001` | Validates, authenticates, deduplicates, stores, and processes incoming webhook events |

The Sender simulates a payment platform (or any event producer). The Receiver simulates a customer system that subscribes to those events.

Together they implement a realistic webhook pipeline:

```
Event creation → Payload contract → Delivery tracking → Retries → Idempotency → HMAC authentication → Timestamp validation
```

This is intentionally **not** a single monolithic app. Real webhook systems are almost always distributed: one service emits events, another service consumes them, and both sides must agree on format, security, and reliability rules.

---

## What This Project Demonstrates

### For managers

- How webhook integrations are structured in practice
- Why authentication, idempotency, and delivery history matter
- What “done” looks like for a webhook feature (not just “we have an endpoint”)
- The difference between a demo endpoint and a production-ready webhook receiver

### For developers

- Building a versioned webhook event contract
- Persisting outbound delivery attempts with status, timing, and response bodies
- Implementing receiver-side validation and structured error responses
- Idempotent event processing using unique event IDs
- HMAC-SHA256 request signing and verification
- Timestamp-based replay protection
- Signing the **raw HTTP body** (a critical implementation detail)
- Using environment variables for shared secrets

---

## Architecture Overview

```
                         WEBHOOK_SECRET
                        /              \
                       /                \
                      ▼                  ▼
               ┌─────────────┐    ┌─────────────┐
               │   SENDER    │    │  RECEIVER   │
               │  :8000      │    │  :8001      │
               └──────┬──────┘    └──────▲──────┘
                      │                  │
                      │  POST /webhooks/events/
                      │  + JSON body
                      │  + signed headers
                      └──────────────────┘
```

### Sender responsibilities

1. Create a `WebhookEvent` with a UUID
2. Build a versioned JSON payload
3. Serialize the payload to exact bytes
4. Generate an HMAC signature from `timestamp + event_id + raw_body`
5. Create a `WebhookDelivery` record
6. POST the signed request to the Receiver
7. Store response status, body, duration, and success/failure

### Receiver responsibilities

1. Validate HTTP method and content type
2. Require authentication headers
3. Validate timestamp freshness (±5 minutes)
4. Verify HMAC signature **before** parsing business logic
5. Parse and validate JSON payload against the event contract
6. Ensure headers match payload fields
7. Enforce idempotency (duplicate events return 200 without reprocessing)
8. Save and process the event

### Security chain on the Receiver

```
REQUEST
   │
   ▼
HTTP method (POST only)
   │
   ▼
Content-Type (application/json)
   │
   ▼
Required auth headers present?
   │
   ▼
Timestamp fresh?
   │
   ▼
HMAC signature valid?
   │
   ▼
Parse JSON + validate contract
   │
   ▼
Header/payload consistency
   │
   ▼
Idempotency check
   │
   ▼
Save + process event
   │
   ▼
200 OK
```

If authentication fails at any point, the Receiver returns **401** and does **not** save or process the event.

---

## Repository Structure

```
django-webhook-lab/
├── README.md
├── requirements.txt          # Shared Python dependencies
├── fake_webhook.py           # Script to test unauthorized webhook requests
│
├── sender/                   # Webhook producer (port 8000)
│   ├── .env                  # Local secrets (not committed)
│   ├── .env.example          # Template for WEBHOOK_SECRET
│   ├── manage.py
│   ├── sender/
│   │   ├── settings.py       # Loads WEBHOOK_SECRET from .env
│   │   └── urls.py
│   ├── core/
│   │   └── views.py          # Health/hello endpoint
│   └── webhooks/
│       ├── models.py         # WebhookEvent, WebhookDelivery
│       ├── views.py          # send_webhook view
│       ├── services.py       # deliver_webhook, retry_delivery
│       ├── security.py       # generate_signature
│       ├── admin.py
│       └── urls.py
│
└── receiver/                 # Webhook consumer (port 8001)
    ├── .env                  # Local secrets (must match Sender)
    ├── .env.example
    ├── manage.py
    ├── receiver/
    │   ├── settings.py
    │   └── urls.py
    ├── core/
    │   └── views.py          # hello, echo test endpoints
    └── webhooks/
        ├── models.py         # WebhookEvent (received events)
        ├── views.py          # receive_webhook view
        ├── security.py       # generate_signature, verify_signature, is_timestamp_valid
        ├── admin.py
        └── urls.py
```

Each app has its own SQLite database (`db.sqlite3`), created when you run migrations.

---

## Prerequisites

- **Python 3.10+** (tested with Python 3.12)
- **pip**
- Two terminal windows (one per Django server)
- Basic familiarity with Django and HTTP

---

## Getting Started

### 1. Clone the repository

```bash
git clone <repository-url>
cd django-webhook-lab
```

### 2. Create and activate a virtual environment

From the repository root:

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS / Linux
python -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

Dependencies include:

- `Django==6.1`
- `requests` — outbound HTTP from Sender
- `python-dotenv` — load secrets from `.env` files

### 4. Configure environment variables

Copy the example env files and set a shared webhook secret.

**Sender:**

```bash
copy sender\.env.example sender\.env        # Windows
# cp sender/.env.example sender/.env       # macOS / Linux
```

**Receiver:**

```bash
copy receiver\.env.example receiver\.env    # Windows
# cp receiver/.env.example receiver/.env   # macOS / Linux
```

Edit both `.env` files so they contain the **same** secret:

```env
WEBHOOK_SECRET=super-secret-webhook-key-123
```

For local development, a simple shared string is fine. For production, generate a long random secret (see [Environment Variables and Secrets](#environment-variables-and-secrets)).

> **Important:** Never commit `.env` files. They are listed in `.gitignore`.

### 5. Run database migrations

Run migrations separately for each project:

```bash
cd sender
python manage.py migrate
cd ..

cd receiver
python manage.py migrate
cd ..
```

### 6. (Optional) Create Django admin users

Useful for inspecting events and deliveries in the browser:

```bash
cd sender
python manage.py createsuperuser

cd ../receiver
python manage.py createsuperuser
```

---

## Environment Variables and Secrets

| Variable | Required | Description |
|---|---|---|
| `WEBHOOK_SECRET` | Yes | Shared HMAC signing secret used by both Sender and Receiver |

Both applications load this from their respective `.env` file via `python-dotenv` in `settings.py`.

### Generate a production-quality secret

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Example output:

```
xK9mP2vL8nQ4rT6wY1zA3bC5dE7fG9hJ0kM2nP4qR6
```

Put the **same value** in:

- `sender/.env`
- `receiver/.env`

Then restart both servers.

### Secret vs Django SECRET_KEY

These are different settings:

| Setting | Purpose |
|---|---|
| `SECRET_KEY` in `settings.py` | Django internal use (sessions, CSRF, etc.) |
| `WEBHOOK_SECRET` in `.env` | HMAC signing between Sender and Receiver |

Do not confuse them.

---

## Running the Applications

You need **both servers running at the same time**.

### Terminal 1 — Sender (port 8000)

```bash
cd sender
python manage.py runserver 8000
```

### Terminal 2 — Receiver (port 8001)

```bash
cd receiver
python manage.py runserver 8001
```

### Quick smoke test

Open in a browser or use curl:

```bash
curl "http://127.0.0.1:8000/webhooks/send/?type=payment.completed"
```

Expected result:

- Sender returns JSON with `"success": true` and `"receiver_status": 200`
- Receiver terminal shows signature verification **PASSED**
- A new event appears in both databases

---

## End-to-End Webhook Flow

### Step-by-step (happy path)

1. Developer or system hits `GET /webhooks/send/?type=payment.completed` on the Sender
2. Sender creates a `WebhookEvent` with a new UUID
3. Sender builds the JSON payload (version `v1`)
4. Sender serializes payload to compact JSON bytes: `separators=(",", ":")`
5. Sender generates Unix timestamp and HMAC signature
6. Sender creates a `WebhookDelivery` record (stores payload, headers, destination URL)
7. Sender POSTs the **exact signed bytes** to `http://127.0.0.1:8001/webhooks/events/`
8. Receiver validates method, content type, headers, timestamp, and signature
9. Receiver parses JSON and validates the event contract
10. Receiver checks idempotency by `event_id`
11. Receiver saves the event and marks it `processed`
12. Receiver returns `200 OK`
13. Sender records delivery success, HTTP status, response body, and duration

### Why the Sender signs raw bytes

Cryptographic signatures operate on exact bytes. If the Sender signs one JSON representation but sends another (different spacing, key order, etc.), verification fails.

This project avoids that by:

1. Serializing once: `raw_body = json.dumps(payload, separators=(",", ":")).encode()`
2. Signing `raw_body`
3. Sending the same `raw_body` in the HTTP request

---

## Webhook Event Contract

Every webhook follows this JSON structure:

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "type": "payment.completed",
  "version": "v1",
  "created_at": "2026-08-31T08:47:25.378568+00:00",
  "source": "webhook-lab-sender",
  "data": {
    "payment": {
      "payment_id": "pay_123",
      "amount": 1500,
      "currency": "NPR"
    }
  }
}
```

### Field reference

| Field | Type | Required | Description |
|---|---|---|---|
| `id` | UUID string | Yes | Globally unique event identifier |
| `type` | string | Yes | Event type (see supported types below) |
| `version` | string | Yes | Contract version (currently `v1`) |
| `created_at` | ISO 8601 datetime | Yes | When the event was created |
| `source` | string | Yes | Must be `webhook-lab-sender` |
| `data` | object | Yes | Event-specific payload |

### Supported event types

| Event Type | Description |
|---|---|
| `payment.created` | A payment was initiated |
| `payment.completed` | A payment completed successfully |
| `payment.failed` | A payment failed |

### Supported versions

| Version | Status |
|---|---|
| `v1` | Active |

---

## HTTP Headers

Every webhook delivery includes these headers:

| Header | Example | Purpose |
|---|---|---|
| `Content-Type` | `application/json` | Declares JSON body |
| `X-Webhook-ID` | `550e8400-e29b-41d4-a716-446655440000` | Event UUID (must match payload `id`) |
| `X-Webhook-Event` | `payment.completed` | Event type (must match payload `type`) |
| `X-Webhook-Version` | `v1` | Contract version (must match payload `version`) |
| `X-Webhook-Timestamp` | `1756620000` | Unix timestamp when request was signed |
| `X-Webhook-Signature` | `sha256=9f8a7c...` | HMAC-SHA256 signature |

### Example request

```http
POST /webhooks/events/ HTTP/1.1
Host: 127.0.0.1:8001
Content-Type: application/json
X-Webhook-ID: 550e8400-e29b-41d4-a716-446655440000
X-Webhook-Event: payment.completed
X-Webhook-Version: v1
X-Webhook-Timestamp: 1756620000
X-Webhook-Signature: sha256=9f8a7c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8

{"id":"550e8400-e29b-41d4-a716-446655440000","type":"payment.completed","version":"v1",...}
```

---

## Security Model

### HMAC-SHA256 authentication

Both Sender and Receiver share `WEBHOOK_SECRET`.

**Message signed:**

```
{timestamp}.{event_id}.{raw_body_bytes}
```

**Algorithm:**

```
signature = HMAC-SHA256(WEBHOOK_SECRET, message)
header value = "sha256=" + hex(signature)
```

HMAC provides:

- **Authentication** — only parties with the secret can produce a valid signature
- **Integrity** — any change to timestamp, event ID, or body invalidates the signature

HMAC does **not** encrypt the payload. The Receiver can still read the JSON body.

### Timestamp validation (replay protection)

The Receiver rejects timestamps outside a **5-minute window** (`TIMESTAMP_TOLERANCE_SECONDS = 300`).

This prevents obviously stale replayed requests. It does not fully stop immediate replays — that is why idempotency is also required.

### Idempotency

The Receiver stores each `event_id` uniquely. If the same valid webhook is delivered twice:

- First delivery → processed normally
- Second delivery → `200 OK` with `"duplicate": true`, business logic does not run again

### Constant-time comparison

Signature verification uses `hmac.compare_digest()` instead of `==` to reduce timing attack risk.

### What HMAC does not solve (yet)

| Threat | Mitigation in this project | Production extension |
|---|---|---|
| Fake requests without secret | HMAC | Per-client secrets |
| Payload tampering | HMAC over raw body | Same |
| Old replayed requests | Timestamp window | Shorter window + nonce store |
| Immediate duplicate replays | Idempotency | Same |
| One compromised integration affecting all clients | Single shared secret | Per-client secrets |

---

## Database Models

### Sender — `WebhookEvent`

| Field | Type | Description |
|---|---|---|
| `event_id` | UUID | Unique event identifier |
| `event_type` | string | e.g. `payment.completed` |
| `payload` | JSON | Business data sent in `data` field |
| `created_at` | datetime | Auto-set on creation |

### Sender — `WebhookDelivery`

Tracks each outbound HTTP attempt for an event.

| Field | Type | Description |
|---|---|---|
| `event` | FK → WebhookEvent | Parent event |
| `destination_url` | URL | Receiver endpoint |
| `payload` | JSON | Full webhook JSON sent |
| `request_headers` | JSON | Headers including signature |
| `attempt_number` | int | Delivery attempt (1, 2, 3...) |
| `status` | string | `pending`, `sending`, `success`, `failed` |
| `sent_at` | datetime | When request was sent |
| `completed_at` | datetime | When attempt finished |
| `duration_ms` | float | Request duration in milliseconds |
| `response_status` | int | HTTP status from Receiver |
| `response_body` | text | Response body from Receiver |
| `success` | bool | Whether delivery succeeded |
| `error_message` | text | Network or exception details |
| `next_retry_at` | datetime | Reserved for retry scheduling |

### Receiver — `WebhookEvent`

| Field | Type | Description |
|---|---|---|
| `event_id` | string (unique) | Event UUID from webhook |
| `event_type` | string | Event type |
| `payload` | JSON | Full received webhook JSON |
| `received_at` | datetime | When webhook was received |
| `processed_at` | datetime | When processing completed |
| `status` | string | `received`, `processing`, `processed` |
| `error_message` | text | Processing errors (if any) |

---

## API Endpoints

### Sender

| Method | URL | Description |
|---|---|---|
| GET | `/webhooks/send/` | Create and deliver a webhook event |
| GET | `/webhooks/send/?type=payment.failed` | Send a specific event type |
| GET | `/hello/` | Simple health/hello response |
| — | `/admin/` | Django admin for events and deliveries |

**Example success response from `/webhooks/send/`:**

```json
{
  "success": true,
  "event_id": "550e8400-e29b-41d4-a716-446655440000",
  "delivery_id": 1,
  "attempt_number": 1,
  "receiver_status": 200,
  "receiver_response": {
    "success": true,
    "message": "Webhook received and processed successfully.",
    "event": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "type": "payment.completed",
      "version": "v1"
    }
  }
}
```

### Receiver

| Method | URL | Description |
|---|---|---|
| POST | `/webhooks/events/` | Receive and process webhook events |
| GET | `/hello/` | Health endpoint with status simulation |
| POST | `/echo/` | Debug endpoint that echoes JSON back |
| — | `/admin/` | Django admin for received events |

### Receiver error response format

All errors follow a consistent structure:

```json
{
  "success": false,
  "error": {
    "code": "invalid_signature",
    "message": "Webhook signature verification failed."
  }
}
```

### Receiver error codes

| HTTP Status | Code | When |
|---|---|---|
| 401 | `missing_timestamp` | No `X-Webhook-Timestamp` header |
| 401 | `missing_signature` | No `X-Webhook-Signature` header |
| 401 | `missing_event_id` | No `X-Webhook-ID` header |
| 401 | `invalid_timestamp` | Timestamp too old, in the future, or not a number |
| 401 | `invalid_signature` | HMAC verification failed |
| 405 | `method_not_allowed` | Not a POST request |
| 415 | `invalid_content_type` | Content-Type is not JSON |
| 400 | `invalid_json` | Body is not valid JSON |
| 400 | `invalid_payload` | JSON root is not an object |
| 400 | `missing_fields` | Required payload fields missing |
| 400 | `invalid_event_id` | `id` is not a valid UUID |
| 400 | `unsupported_event_type` | Unknown event type |
| 400 | `unsupported_version` | Unknown contract version |
| 400 | `invalid_source` | `source` is not `webhook-lab-sender` |
| 400 | `invalid_data` | `data` is not a JSON object |
| 400 | `event_id_mismatch` | Header ID ≠ payload `id` |
| 400 | `event_type_mismatch` | Header type ≠ payload `type` |
| 400 | `version_mismatch` | Header version ≠ payload `version` |

---

## Django Admin

Both apps expose models in Django Admin.

### Sender admin (`http://127.0.0.1:8000/admin/`)

- **Webhook Events** — view created events and delivery count
- **Webhook Deliveries** — inspect attempt number, status, HTTP response, duration, headers (including signature)

Useful for debugging: open a delivery and check `request_headers` to see the exact `X-Webhook-Signature` that was sent.

### Receiver admin (`http://127.0.0.1:8001/admin/`)

- **Webhook Events** — view received events, status, and processing timestamps

---

## Testing Guide

### Test 1 — Valid webhook (authentication works)

```bash
curl "http://127.0.0.1:8000/webhooks/send/?type=payment.completed"
```

Expected:

- Sender: `"success": true`, `"receiver_status": 200`
- Receiver console: `Signature verification: PASSED`

### Test 2 — Wrong secret

1. Change `WEBHOOK_SECRET` in `receiver/.env` to a different value
2. Restart Receiver only
3. Send webhook again

Expected:

- Sender: `"receiver_status": 401`
- Receiver: `"code": "invalid_signature"`

Restore the matching secret afterward.

### Test 3 — Fake / unauthorized webhook

From the repository root (Receiver must be running):

```bash
python fake_webhook.py
```

Expected:

- HTTP `401`
- `"code": "invalid_signature"`

This simulates an attacker who knows the URL but not the secret.

### Test 4 — Missing signature

Edit `fake_webhook.py` and remove the `X-Webhook-Signature` header.

Expected: `401` with `"code": "missing_signature"`

### Test 5 — Idempotency

Send the same event twice by triggering `/webhooks/send/` twice. Each call creates a **new** event with a new UUID, so to test true idempotency you would need to replay the exact same request (same body, headers, and signature within the timestamp window).

Alternatively, inspect Receiver admin after sending once — resending an identical captured request should return:

```json
{
  "success": true,
  "message": "Webhook already processed.",
  "duplicate": true
}
```

### Test 6 — Different event types

```bash
curl "http://127.0.0.1:8000/webhooks/send/?type=payment.created"
curl "http://127.0.0.1:8000/webhooks/send/?type=payment.failed"
```

### Test 7 — Receiver echo endpoint (debugging)

```bash
curl -X POST http://127.0.0.1:8001/echo/ \
  -H "Content-Type: application/json" \
  -d "{\"hello\": \"world\"}"
```

---

## Troubleshooting

### `401 invalid_signature` on valid requests

| Cause | Fix |
|---|---|
| Secrets differ between Sender and Receiver | Ensure identical `WEBHOOK_SECRET` in both `.env` files |
| Server not restarted after `.env` change | Restart both Django servers |
| Body bytes mismatch | Sender must sign and send the same serialized JSON (`separators=(",", ":")`) |

### `401 invalid_timestamp`

| Cause | Fix |
|---|---|
| System clock skew | Sync system time |
| Replaying an old captured request | Use a fresh request from `/webhooks/send/` |
| Timestamp header is not a Unix integer | Must be seconds since epoch, e.g. `1756620000` |

### Connection refused / Sender returns 502

| Cause | Fix |
|---|---|
| Receiver not running | Start Receiver on port 8001 |
| Wrong destination URL | Sender posts to `http://127.0.0.1:8001/webhooks/events/` |

### `ModuleNotFoundError: No module named 'dotenv'`

```bash
pip install python-dotenv
```

Or reinstall from `requirements.txt`.

### Migrations missing

```bash
cd sender && python manage.py migrate
cd ../receiver && python manage.py migrate
```

### `.env` not loading

Both `settings.py` files call:

```python
load_dotenv(BASE_DIR / ".env")
```

Ensure `.env` exists in `sender/` and `receiver/` respectively (not only at repo root).

---

## Implementation Stages

This project was built incrementally across learning stages:

| Stage | Feature |
|---|---|
| 1 | Basic Sender → Receiver HTTP POST |
| 2 | Structured webhook event contract (versioned JSON) |
| 3 | Receiver validation with structured error responses |
| 4 | Sender delivery model and delivery history |
| 5 | Retry concept (`retry_delivery`, attempt numbers, retryable status codes) |
| 6 | Receiver event persistence and processing lifecycle |
| 7 | Idempotency using unique event IDs |
| 8 | HMAC-SHA256 authentication + timestamp replay protection |

Each stage adds one production concern. Together they form a realistic webhook foundation.

---

## Production Considerations

This is a **learning lab**, not a production deployment. Before using these patterns in production, consider:

1. **Per-client secrets** — one global secret is fine for learning; production systems should use a unique secret per integration
2. **Secret rotation** — plan for rotating secrets without downtime
3. **Async delivery** — use a task queue (Celery, RQ, etc.) instead of synchronous HTTP in the request cycle
4. **Automatic retries** — `retry_delivery()` exists but is not wired to a scheduler; production needs background workers
5. **HTTPS only** — never send signed webhooks over plain HTTP in production
6. **Monitoring and alerting** — track delivery failure rates, latency, and signature failures
7. **Webhook subscription management** — customers need UI/API to register endpoints and rotate secrets
8. **Rate limiting** — protect the Receiver from abuse
9. **Dead letter queue** — persist events that fail after all retries
10. **IP allowlisting** — optional additional layer (not a substitute for HMAC)

---

## Tech Stack

| Component | Technology |
|---|---|
| Framework | Django 6.1 |
| Database | SQLite (local development) |
| HTTP client | requests |
| Configuration | python-dotenv |
| Signing | HMAC-SHA256 (Python standard library) |
| Language | Python 3.10+ |

---

## Quick Reference

```bash
# Setup
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
copy sender\.env.example sender\.env
copy receiver\.env.example receiver\.env
cd sender && python manage.py migrate && cd ..
cd receiver && python manage.py migrate && cd ..

# Run (two terminals)
cd sender && python manage.py runserver 8000
cd receiver && python manage.py runserver 8001

# Send a webhook
curl "http://127.0.0.1:8000/webhooks/send/?type=payment.completed"

# Test fake/attacker request
python fake_webhook.py
```

---

## License

Add your license here if applicable.
