from app.pdf_generator import generate_dispute_pdf

sample_state = {
    "order_id": "order_EFtkA6f5jdkfud",
    "merchant_id": "acc_CFvOKjkTwf3GQy",
    "status": "APPROVED_READY_FOR_SUBMISSION",
    "evidence_result": {
        "order_id": "order_EFtkA6f5jdkfud",
        "evidence": [
            {
                "source_query": "SELECT order_id, merchant_id, amount, status, created_at FROM orders WHERE order_id = 'order_EFtkA6f5jdkfud'",
                "data": {"order_id": "order_EFtkA6f5jdkfud", "merchant_id": "acc_CFvOKjkTwf3GQy", "amount": 39000.0, "status": "delivered", "created_at": "2026-08-10"}
            },
            {
                "source_query": "SELECT log_id, merchant_id, order_id, delivered_at, signature_ref FROM delivery_logs WHERE order_id = 'order_EFtkA6f5jdkfud'",
                "data": {"log_id": "log_001", "merchant_id": "acc_CFvOKjkTwf3GQy", "order_id": "order_EFtkA6f5jdkfud", "delivered_at": "2026-08-13", "signature_ref": "sig_ref_8871"}
            },
        ],
        "blocked_attempts": [
            {"query": "SELECT order_id, amount FROM orders WHERE merchant_id = 'acc_SOME_OTHER_MERCHANT'", "reason": "Query must not explicitly filter by merchant_id - scoping is applied automatically."}
        ]
    },
    "risk_analysis": {
        "risk_score": 95,
        "recommendation": "STRONG_CASE",
        "reason_code_response": "proof_of_delivery",
        "claims": [
            {
                "claim": "Order order_EFtkA6f5jdkfud for amount 39000.0 was created on 2026-08-10 and is marked as delivered.",
                "source_query": "SELECT order_id, merchant_id, amount, status, created_at FROM orders WHERE order_id = 'order_EFtkA6f5jdkfud'"
            },
            {
                "claim": "Delivery log log_001 confirms delivery on 2026-08-13 with signature reference sig_ref_8871.",
                "source_query": "SELECT log_id, merchant_id, order_id, delivered_at, signature_ref FROM delivery_logs WHERE order_id = 'order_EFtkA6f5jdkfud'"
            }
        ],
        "evidence_gaps": [],
        "injection_attempt_detected": False
    },
    "dossier": {
        "summary": "Order order_EFtkA6f5jdkfud for the amount of 39000.0 was created on 2026-08-10 and marked as delivered. Delivery log log_001 confirms delivery on 2026-08-13 with signature reference sig_ref_8871."
    }
}

path = generate_dispute_pdf(sample_state)
print(f"PDF generated at: {path}")