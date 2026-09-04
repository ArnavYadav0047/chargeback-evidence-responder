import pickle
import pandas as pd
from langgraph.graph import StateGraph, END
from typing import TypedDict
from src.evidence_writer import gather_evidence, write_evidence_packet
from src.decision import make_decision
import sqlite3
import json
from datetime import datetime

# --- State definition ---
class CaseState(TypedDict):
    case: dict
    evidence: dict
    risk_score: float
    decision_result: dict
    packet: str

# --- Load model once ---
with open("models/risk_model.pkl", "rb") as f:
    RISK_MODEL = pickle.load(f)

FEATURES = [
    "amount", "delivery_confirmed", "ip_location_match",
    "device_fingerprint_match", "customer_order_history",
    "days_to_dispute", "chargeback_fee", "cost_of_goods"
]

# --- Audit log setup ---
def init_db():
    conn = sqlite3.connect("audit.db")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_id TEXT,
            risk_score REAL,
            decision TEXT,
            ev_fight REAL,
            ev_concede REAL,
            reason TEXT,
            packet TEXT,
            timestamp TEXT
        )
    """)
    conn.commit()
    conn.close()

def log_to_db(state: CaseState):
    conn = sqlite3.connect("audit.db")
    conn.execute("""
        INSERT INTO audit_log
        (case_id, risk_score, decision, ev_fight, ev_concede, reason, packet, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        state["case"]["case_id"],
        state["risk_score"],
        state["decision_result"]["decision"],
        state["decision_result"]["ev_fight"],
        state["decision_result"]["ev_concede"],
        state["decision_result"]["reason"],
        state["packet"],
        datetime.now().isoformat()
    ))
    conn.commit()
    conn.close()

# --- LangGraph nodes ---
def node_gather_evidence(state: CaseState) -> CaseState:
    state["evidence"] = gather_evidence(state["case"])
    return state

def node_score_risk(state: CaseState) -> CaseState:
    case = state["case"]
    # Handle missing fields gracefully
    for f in FEATURES:
        if case.get(f) is None:
            state["risk_score"] = 0.5  # default to uncertain
            return state
    row = pd.DataFrame([{f: case[f] for f in FEATURES}])
    state["risk_score"] = float(RISK_MODEL.predict_proba(row)[0][1])
    return state

def node_decide(state: CaseState) -> CaseState:
    state["decision_result"] = make_decision(
        state["risk_score"],
        state["case"]["amount"],
        state["case"]["cost_of_goods"]
    )
    return state

def node_write_packet(state: CaseState) -> CaseState:
    state["packet"] = write_evidence_packet(
        state["evidence"],
        state["decision_result"]["decision"]
    )
    return state

def node_log(state: CaseState) -> CaseState:
    log_to_db(state)
    return state

# --- Build graph ---
def build_pipeline():
    graph = StateGraph(CaseState)
    graph.add_node("gather_evidence", node_gather_evidence)
    graph.add_node("score_risk", node_score_risk)
    graph.add_node("decide", node_decide)
    graph.add_node("write_packet", node_write_packet)
    graph.add_node("log", node_log)

    graph.set_entry_point("gather_evidence")
    graph.add_edge("gather_evidence", "score_risk")
    graph.add_edge("score_risk", "decide")
    graph.add_edge("decide", "write_packet")
    graph.add_edge("write_packet", "log")
    graph.add_edge("log", END)

    return graph.compile()


if __name__ == "__main__":
    init_db()
    pipeline = build_pipeline()

    test_case = {
        "case_id": "CB_TEST_001",
        "amount": 6500,
        "delivery_confirmed": True,
        "ip_location_match": True,
        "device_fingerprint_match": True,
        "customer_order_history": 8,
        "days_to_dispute": 30,
        "payment_method": "upi",
        "chargeback_fee": 250,
        "cost_of_goods": 6000
    }

    result = pipeline.invoke({"case": test_case})

    print(f"\nCase ID   : {result['case']['case_id']}")
    print(f"Risk Score: {result['risk_score']:.2f}")
    print(f"Decision  : {result['decision_result']['decision']}")
    print(f"Reason    : {result['decision_result']['reason']}")
    print(f"\nPacket:\n{result['packet']}")
    print("\n✅ Logged to audit.db")