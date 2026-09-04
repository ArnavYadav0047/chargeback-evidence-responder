import streamlit as st
import pickle
import pandas as pd
import sqlite3
from datetime import datetime
from src.evidence_writer import gather_evidence, write_evidence_packet
from src.decision import make_decision

# --- Load model ---
with open("models/risk_model.pkl", "rb") as f:
    RISK_MODEL = pickle.load(f)

FEATURES = [
    "amount", "delivery_confirmed", "ip_location_match",
    "device_fingerprint_match", "customer_order_history",
    "days_to_dispute", "chargeback_fee", "cost_of_goods"
]

def score_risk(case):
    row = pd.DataFrame([{f: case[f] for f in FEATURES}])
    return float(RISK_MODEL.predict_proba(row)[0][1])

def log_to_db(case_id, risk_score, decision, ev_fight, ev_concede, reason, packet):
    conn = sqlite3.connect("audit.db")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_id TEXT, risk_score REAL, decision TEXT,
            ev_fight REAL, ev_concede REAL, reason TEXT, packet TEXT, timestamp TEXT
        )
    """)
    conn.execute("""
        INSERT INTO audit_log
        (case_id, risk_score, decision, ev_fight, ev_concede, reason, packet, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (case_id, risk_score, decision, ev_fight, ev_concede, reason, packet, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def get_audit_log():
    conn = sqlite3.connect("audit.db")
    try:
        df = pd.read_sql("SELECT * FROM audit_log ORDER BY id DESC", conn)
    except:
        df = pd.DataFrame()
    conn.close()
    return df

# --- UI ---
st.set_page_config(page_title="Chargeback Evidence Responder", layout="wide")
st.title("⚖️ Chargeback Evidence Responder")
st.caption("AI-powered dispute decisioning on Razorpay rails")

st.subheader("Enter Dispute Details")

col1, col2 = st.columns(2)
with col1:
    case_id = st.text_input("Case ID", value="CB_001")
    amount = st.number_input("Transaction Amount (₹)", min_value=0.0, value=5000.0)
    cost_of_goods = st.number_input("Cost of Goods (₹)", min_value=0.0, value=4500.0)
    payment_method = st.selectbox("Payment Method", ["upi", "card", "netbanking"])

with col2:
    delivery_confirmed = st.checkbox("Delivery Confirmed", value=True)
    ip_location_match = st.checkbox("IP Location Match", value=True)
    device_fingerprint_match = st.checkbox("Device Fingerprint Match", value=True)
    customer_order_history = st.number_input("Past Orders by Customer", min_value=0, value=5)
    days_to_dispute = st.number_input("Days to Dispute", min_value=1, value=20)

if st.button("🔍 Analyse Dispute", use_container_width=True):
    case = {
        "case_id": case_id,
        "amount": amount,
        "cost_of_goods": cost_of_goods,
        "payment_method": payment_method,
        "delivery_confirmed": delivery_confirmed,
        "ip_location_match": ip_location_match,
        "device_fingerprint_match": device_fingerprint_match,
        "customer_order_history": customer_order_history,
        "days_to_dispute": days_to_dispute,
        "chargeback_fee": 250
    }

    with st.spinner("Running pipeline..."):
        risk_score = score_risk(case)
        decision_result = make_decision(risk_score, amount, cost_of_goods)
        evidence = gather_evidence(case)
        packet = write_evidence_packet(evidence, decision_result["decision"])
        log_to_db(case_id, risk_score, decision_result["decision"],
                  decision_result["ev_fight"], decision_result["ev_concede"],
                  decision_result["reason"], packet)

    st.divider()
    col3, col4, col5 = st.columns(3)
    col3.metric("Risk Score", f"{risk_score:.0%}")
    col4.metric("Decision", decision_result["decision"])
    col5.metric("EV(fight) vs EV(concede)", f"₹{decision_result['ev_fight']} vs ₹{decision_result['ev_concede']}")

    st.info(decision_result["reason"])

    st.subheader("📄 Evidence Packet")
    st.write(packet)

st.divider()
st.subheader("🗂️ Audit Log")
df = get_audit_log()
if df.empty:
    st.caption("No cases logged yet.")
else:
    st.dataframe(df, use_container_width=True)