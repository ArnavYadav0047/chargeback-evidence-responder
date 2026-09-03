import pandas as pd
import numpy as np
import random
import os

np.random.seed(42)
random.seed(42)

def make_decision(risk_score: float, amount: float, cost_of_goods: float, chargeback_fee: float = 250) -> dict:
    prob_fraud = risk_score
    prob_legit = 1 - risk_score
    admin_cost = 150

    ev_fight = (prob_fraud * amount) - (prob_legit * chargeback_fee) - admin_cost
    ev_concede = -admin_cost * 0.3  # conceding costs only a small processing fee, not full goods

    decision = "FIGHT" if ev_fight > ev_concede else "CONCEDE"
    reason = (
        f"EV(fight)=₹{ev_fight:.2f} vs EV(concede)=₹{ev_concede:.2f}. "
        f"Fraud probability: {prob_fraud:.0%}. "
        f"{'Fighting is profitable.' if decision == 'FIGHT' else 'Conceding is cheaper.'}"
    )

    return {
        "decision": decision,
        "ev_fight": round(ev_fight, 2),
        "ev_concede": round(ev_concede, 2),
        "fraud_probability": round(prob_fraud, 3),
        "reason": reason
    }


if __name__ == "__main__":
    cases = [
        {"risk_score": 0.92, "amount": 8000, "cost_of_goods": 7500, "label": "Should FIGHT"},
        {"risk_score": 0.03, "amount": 300,  "cost_of_goods": 280,  "label": "Should CONCEDE"},
        {"risk_score": 0.55, "amount": 500,  "cost_of_goods": 450,  "label": "Borderline"},
    ]

    for c in cases:
        result = make_decision(c["risk_score"], c["amount"], c["cost_of_goods"])
        print(f"\n[{c['label']}]")
        print(f"  Decision : {result['decision']}")
        print(f"  Reason   : {result['reason']}")