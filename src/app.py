import streamlit as st
import pickle
import pandas as pd
import sqlite3
import sys, os
from datetime import datetime
sys.path.insert(0, os.path.dirname(__file__))
from evidence_writer import gather_evidence, write_evidence_packet
from decision import make_decision

model_path = os.path.join(os.path.dirname(__file__), "..", "models", "risk_model.pkl")
with open(model_path, "rb") as f:
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

st.set_page_config(page_title="Chargeback Evidence Responder", layout="wide", page_icon="⚖️")

st.markdown("""
<style>
    .header-bar {
        background: linear-gradient(90deg, #2563EB 0%, #1E40AF 100%);
        padding: 1.5rem 2rem;
        border-radius: 12px;
        margin-bottom: 2rem;
    }
    .header-bar h1 { color: white; margin: 0; font-size: 1.8rem; }
    .header-bar p { color: #BFDBFE; margin: 0.25rem 0 0 0; font-size: 0.9rem; }
    .section-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
    }
    .section-title {
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.1em;
        color: #64748B;
        text-transform: uppercase;
        margin-bottom: 1rem;
    }
    .decision-fight {
        background: #DCFCE7;
        border-left: 4px solid #16A34A;
        padding: 1rem 1.5rem;
        border-radius: 8px;
        font-weight: 600;
        color: #15803D;
    }
    .decision-concede {
        background: #FEF9C3;
        border-left: 4px solid #CA8A04;
        padding: 1rem 1.5rem;
        border-radius: 8px;
        font-weight: 600;
        color: #92400E;
    }
    .packet-box {
        background: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 1.25rem;
        font-size: 0.95rem;
        line-height: 1.7;
        color: #1E293B;
    }
    .stButton > button {
        background: #2563EB !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.6rem 2rem !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
    }
    .stButton > button:hover {
        background: #1D4ED8 !important;
    }
    div[data-testid="metric-container"] {
        background: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div class="header-bar">
    <h1>⚖️ Chargeback Evidence Responder</h1>
    <p>AI-powered dispute decisioning built on Razorpay rails · Track 02 — AI Risk Manager</p>
</div>
""", unsafe_allow_html=True)

# Input form
st.markdown('<div class="section-card">', unsafe_allow_html=True)
st.markdown('<div class="section-title">Dispute Details</div>', unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)
with col1:
    case_id = st.text_input("Case ID", value="CB_001")
    amount = st.number_input("Transaction Amount (₹)", min_value=0.0, value=5000.0)
    cost_of_goods = st.number_input("Cost of Goods (₹)", min_value=0.0, value=4500.0)
with col2:
    payment_method = st.selectbox("Payment Method", ["upi", "card", "netbanking"])
    customer_order_history = st.number_input("Past Orders by Customer", min_value=0, value=5)
    days_to_dispute = st.number_input("Days to Dispute", min_value=1, value=20)
with col3:
    st.markdown("**Evidence Signals**")
    delivery_confirmed = st.checkbox("Delivery Confirmed", value=True)
    ip_location_match = st.checkbox("IP Location Match", value=True)
    device_fingerprint_match = st.checkbox("Device Fingerprint Match", value=True)

st.markdown('</div>', unsafe_allow_html=True)

if st.button("Analyse Dispute →", use_container_width=True):
    case = {
        "case_id": case_id, "amount": amount, "cost_of_goods": cost_of_goods,
        "payment_method": payment_method, "delivery_confirmed": delivery_confirmed,
        "ip_location_match": ip_location_match, "device_fingerprint_match": device_fingerprint_match,
        "customer_order_history": customer_order_history, "days_to_dispute": days_to_dispute,
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

    st.markdown("---")
    st.markdown('<div class="section-title">Analysis Results</div>', unsafe_allow_html=True)

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Fraud Risk Score", f"{risk_score:.0%}")
    m2.metric("EV — Fight", f"₹{decision_result['ev_fight']:,.0f}")
    m3.metric("EV — Concede", f"₹{decision_result['ev_concede']:,.0f}")
    m4.metric("Chargeback Fee", "₹250")

    if decision_result["decision"] == "FIGHT":
        st.markdown(f'<div class="decision-fight">✅ Recommendation: FIGHT — {decision_result["reason"]}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="decision-concede">⚠️ Recommendation: CONCEDE — {decision_result["reason"]}</div>', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown('<div class="section-title">Evidence Packet</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="packet-box">{packet}</div>', unsafe_allow_html=True)

st.markdown("---")
st.markdown('<div class="section-title">Audit Log</div>', unsafe_allow_html=True)
df = get_audit_log()
if df.empty:
    st.caption("No cases logged yet.")
else:
    st.dataframe(df[["case_id", "risk_score", "decision", "ev_fight", "ev_concede", "reason", "timestamp"]],
                 use_container_width=True, hide_index=True)