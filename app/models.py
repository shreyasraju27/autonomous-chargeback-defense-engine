from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from sqlalchemy.sql import func
from app.database import Base


class Dispute(Base):
    __tablename__ = "disputes"

    id = Column(Integer, primary_key=True, index=True)
    razorpay_event_id = Column(String, unique=True, index=True)  # for idempotency
    dispute_id = Column(String, index=True)
    payment_id = Column(String, index=True)
    merchant_id = Column(String, index=True)
    amount = Column(Integer)
    currency = Column(String)
    reason_code = Column(String)
    status = Column(String, default="NEW")  # NEW, IN_REVIEW, PENDING_APPROVAL, APPROVED
    respond_by = Column(Integer)  # unix timestamp
    raw_payload = Column(Text)  # full original webhook JSON, stored as text
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Order(Base):
    __tablename__ = "orders"

    order_id = Column(String, primary_key=True, index=True)
    merchant_id = Column(String, index=True)
    amount = Column(Float)
    status = Column(String)
    created_at = Column(String)


class DeliveryLog(Base):
    __tablename__ = "delivery_logs"

    log_id = Column(String, primary_key=True, index=True)
    merchant_id = Column(String, index=True)
    order_id = Column(String, index=True)
    delivered_at = Column(String)
    signature_ref = Column(String)


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    msg_id = Column(String, primary_key=True, index=True)
    merchant_id = Column(String, index=True)
    order_id = Column(String, index=True)
    sender = Column(String)
    body_masked = Column(Text)
    sent_at = Column(String)