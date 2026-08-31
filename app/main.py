import hashlib
import hmac
import json
import time
import uuid

from fastapi import FastAPI, Request, HTTPException, Depends
from sqlalchemy.orm import Session

from app.database import engine, get_db, Base
from app.models import Dispute

# our own secret, standing in for a Razorpay-issued webhook secret
from dotenv import load_dotenv
import os

load_dotenv()

WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")

app = FastAPI(title="Dispute Defense Engine")

# create tables on startup if they don't exist
Base.metadata.create_all(bind=engine)


def generate_signature(body: bytes, secret: str) -> str:
    """Same HMAC-SHA256 method Razorpay uses to sign webhook bodies."""
    return hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


def verify_signature(body: bytes, signature: str, secret: str) -> bool:
    expected = generate_signature(body, secret)
    return hmac.compare_digest(expected, signature)


@app.get("/")
def root():
    return {"status": "Dispute Defense Engine is running"}


@app.post("/mock-trigger")
def mock_trigger():
    """
    Simulates Razorpay sending a payment.dispute.created webhook,
    using the exact payload structure from Razorpay's real docs.
    """
    payload = {
        "entity": "event",
        "account_id": "acc_CFvOKjkTwf3GQy",
        "event": "payment.dispute.created",
        "contains": ["payment", "dispute"],
        "payload": {
            "payment": {
                "entity": {
                    "id": "pay_EFtmUsbwpXwBHI",
                    "entity": "payment",
                    "amount": 529760,
                    "currency": "INR",
                    "status": "captured",
                    "order_id": "order_EFtkA6f5jdkfud",
                    "method": "card",
                    "email": "gaurav.kumar@example.com",
                    "contact": "+919900000000",
                    "created_at": int(time.time())
                }
            },
            "dispute": {
                "entity": {
                    "id": f"disp_{uuid.uuid4().hex[:14]}",
                    "entity": "dispute",
                    "payment_id": "pay_EFtmUsbwpXwBHI",
                    "amount": 39000,
                    "currency": "INR",
                    "reason_code": "goods_or_services_not_received_or_partially_received",
                    "respond_by": int(time.time()) + 7 * 24 * 3600,
                    "status": "open",
                    "phase": "chargeback",
                    "created_at": int(time.time())
                }
            }
        },
        "created_at": int(time.time())
    }

    body_bytes = json.dumps(payload).encode()
    signature = generate_signature(body_bytes, WEBHOOK_SECRET)

    import urllib.request
    req = urllib.request.Request(
        "http://127.0.0.1:8000/webhook/dispute",
        data=body_bytes,
        headers={
            "Content-Type": "application/json",
            "X-Razorpay-Signature": signature
        },
        method="POST"
    )
    with urllib.request.urlopen(req) as resp:
        result = json.loads(resp.read())

    return {"mock_trigger": "sent", "backend_response": result}


@app.post("/webhook/dispute")
async def receive_dispute_webhook(request: Request, db: Session = Depends(get_db)):
    raw_body = await request.body()
    signature = request.headers.get("X-Razorpay-Signature", "")

    if not verify_signature(raw_body, signature, WEBHOOK_SECRET):
        raise HTTPException(status_code=400, detail="Invalid webhook signature")

    payload = json.loads(raw_body)

    event_id = f"{payload.get('event')}_{payload.get('created_at')}_{payload['payload']['dispute']['entity']['id']}"

    # idempotency check
    existing = db.query(Dispute).filter(Dispute.razorpay_event_id == event_id).first()
    if existing:
        return {"status": "duplicate_ignored", "dispute_id": existing.dispute_id}

    dispute_entity = payload["payload"]["dispute"]["entity"]
    payment_entity = payload["payload"]["payment"]["entity"]

    new_dispute = Dispute(
        razorpay_event_id=event_id,
        dispute_id=dispute_entity["id"],
        payment_id=dispute_entity["payment_id"],
        merchant_id=payload.get("account_id", "unknown"),
        amount=dispute_entity["amount"],
        currency=dispute_entity["currency"],
        reason_code=dispute_entity["reason_code"],
        status="NEW",
        respond_by=dispute_entity["respond_by"],
        raw_payload=json.dumps(payload)
    )
    db.add(new_dispute)
    db.commit()
    db.refresh(new_dispute)

    return {
        "status": "received",
        "dispute_id": new_dispute.dispute_id,
        "db_id": new_dispute.id
    }