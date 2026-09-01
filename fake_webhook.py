import requests

payload = """
{"id":"fake-id","type":"payment.completed","version":"v1","created_at":"2026-08-31T14:00:00+05:45","source":"attacker","data":{"payment":{"amount":999999}}}
"""

headers = {
    "Content-Type": "application/json",
    "X-Webhook-ID": "fake-id",
    "X-Webhook-Event": "payment.completed",
    "X-Webhook-Version": "v1",
    "X-Webhook-Timestamp": "1756620000",
    "X-Webhook-Signature": "sha256=fake-signature",
}

response = requests.post(
    "http://127.0.0.1:8001/webhooks/events/",
    data=payload.encode(),
    headers=headers,
)

print(response.status_code)
print(response.text)
