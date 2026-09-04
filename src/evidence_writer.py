from groq import Groq
from dotenv import load_dotenv
import os
import time

load_dotenv()

try:
    import streamlit as st
    api_key = st.secrets["GROQ_API_KEY"]
except Exception:
    api_key = os.environ.get("GROQ_API_KEY")

client = Groq(api_key=api_key)


def gather_evidence(case: dict) -> dict:
    return {
        "case_id": case["case_id"],
        "amount": case["amount"],
        "delivery_confirmed": case["delivery_confirmed"],
        "ip_location_match": case["ip_location_match"],
        "device_fingerprint_match": case["device_fingerprint_match"],
        "customer_order_history": case["customer_order_history"],
        "days_to_dispute": case["days_to_dispute"],
        "payment_method": case["payment_method"],
        "missing_fields": [k for k, v in case.items() if v is None]
    }


def write_evidence_packet(evidence: dict, decision: str) -> str:
    if evidence["missing_fields"]:
        return f"INSUFFICIENT EVIDENCE: Missing fields {evidence['missing_fields']}. Defaulting to CONCEDE."

    if decision == "FIGHT":
        prompt = f"""
You are a chargeback dispute analyst for an Indian payment gateway.
Write a professional, concise dispute response letter based on this evidence:

Case ID: {evidence['case_id']}
Amount: ₹{evidence['amount']}
Delivery Confirmed: {evidence['delivery_confirmed']}
IP Location Match: {evidence['ip_location_match']}
Device Fingerprint Match: {evidence['device_fingerprint_match']}
Customer Order History (past orders): {evidence['customer_order_history']}
Days until dispute was raised: {evidence['days_to_dispute']}
Payment Method: {evidence['payment_method']}

Write 3-4 sentences max. Be factual, reference only the data above. Do not invent details.
"""
    else:
        prompt = f"""
You are a chargeback dispute analyst for an Indian payment gateway.
Write a brief internal note explaining why we are conceding dispute {evidence['case_id']}
for ₹{evidence['amount']}. Reference the weak evidence points. 2 sentences max.
"""

    for attempt in range(3):
        try:
            response = client.chat.completions.create(
                model="qwen/qwen3.8-27b",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300
            )
            return response.choices[0].message.content
        except Exception as e:
            if attempt < 2:
                time.sleep(3)
            else:
                return f"Evidence generation temporarily unavailable. Decision: {decision}. Please retry."


if __name__ == "__main__":
    test_cases = [
        {
            "case_id": "CB_0001",
            "amount": 8000,
            "delivery_confirmed": True,
            "ip_location_match": True,
            "device_fingerprint_match": True,
            "customer_order_history": 12,
            "days_to_dispute": 45,
            "payment_method": "upi"
        },
        {
            "case_id": "CB_0002",
            "amount": 300,
            "delivery_confirmed": False,
            "ip_location_match": False,
            "device_fingerprint_match": None,
            "customer_order_history": 0,
            "days_to_dispute": 2,
            "payment_method": "card"
        }
    ]

    decisions = ["FIGHT", "CONCEDE"]

    for case, decision in zip(test_cases, decisions):
        evidence = gather_evidence(case)
        packet = write_evidence_packet(evidence, decision)
        print(f"\n=== {case['case_id']} | Decision: {decision} ===")
        print(packet)