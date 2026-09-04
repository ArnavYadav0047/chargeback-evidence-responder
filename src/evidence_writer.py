from google import genai
from dotenv import load_dotenv
import os
import time

load_dotenv()

try:
    import streamlit as st
    api_key = st.secrets["GOOGLE_API_KEY"]
except Exception:
    api_key = os.environ.get("GOOGLE_API_KEY")

client = genai.Client(api_key=api_key)


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
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            return response.text
        except Exception as e:
            if attempt < 2:
                time.sleep(3)
            else:
                return f"Evidence generation temporarily unavailable. Decision: {decision}. Please retry in a moment."