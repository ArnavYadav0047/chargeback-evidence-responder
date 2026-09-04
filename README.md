# ⚖️ Chargeback Evidence Responder

AI-powered dispute decisioning built on Razorpay rails — Razorpay AI Buildathon 2026, Track 02: AI Risk Manager.

🔗 **Live Demo**: https://chargeback-evidence-responder-ay.streamlit.app

---

## The Problem

When a customer disputes a payment, the merchant has a limited window to either fight the chargeback with evidence or concede. Today, this is done manually — a human digs through order records, writes a justification, and submits it. It is slow, inconsistent, and costly.

Razorpay's existing stack (Thirdwatch, Shield) handles fraud prevention — scoring transactions before or at the moment of payment. There is no public automated system for post-dispute response: deciding whether to fight or concede, and generating the evidence packet automatically.

This project fills that gap.

---

## What It Does

Given a disputed transaction, the system:

1. **Gathers evidence** — delivery status, IP location match, device fingerprint, customer order history, days to dispute
2. **Scores fraud risk** — LightGBM model outputs a fraud probability (0–1)
3. **Makes a cost-aware decision** — computes Expected Value of fighting vs conceding using real cost parameters (chargeback fee, cost of goods, admin cost), picks the financially optimal action
4. **Writes the evidence packet** — LLM drafts a professional dispute response letter or internal concede note, grounded only in actual evidence
5. **Logs everything** — every decision is written to an audit log with full reasoning, EV calculations, and timestamp

---

## Why This Is Different From Existing Solutions

| | Razorpay Shield/Thirdwatch | Justt/Chargeflow | This Project |
|---|---|---|---|
| Stage | Pre-transaction prevention | Post-dispute (Western rails) | Post-dispute (Razorpay rails) |
| Decision logic | Binary fraud flag | Opaque, black-box | Transparent EV-based math |
| Evidence packet | None | Template-based | LLM-generated, case-specific |
| Audit trail | No | No | Full — every decision inspectable |
| Indian payment context | Yes | No | Yes — UPI, INR, Indian dispute flows |

---

## Architecture

```
Dispute Input
     |
     v
Evidence Gatherer
     |
     v
Risk Scorer (LightGBM) — fraud probability score
     |
     v
Cost-Aware Decision Layer — EV(fight) vs EV(concede) — FIGHT or CONCEDE
     |
     v
Evidence Packet Writer (Groq / Qwen3.8-27b) — dispute letter or concede note
     |
     v
Audit Logger (SQLite) — case_id, risk_score, decision, EV values, reason, timestamp
```

Orchestrated end-to-end using **LangGraph**.

---

## Honest Model Metrics

Trained on 500 synthetic cases modeled on Indian payment patterns (UPI, card, netbanking), with 15% label noise added to simulate real-world overlap.

| Metric | Legit | Fraud |
|---|---|---|
| Precision | 0.79 | 0.78 |
| Recall | 0.86 | 0.69 |
| F1-Score | 0.83 | 0.73 |
| Overall Accuracy | 79% | |

False negatives (fraud missed): 13/100 — the cost-aware decision layer is specifically designed to handle these borderline cases by weighing the financial cost of missing them rather than relying on the classification threshold alone.

Note: Synthetic data produces cleaner separations than real-world data. Production performance would require retraining on real Razorpay transaction data.

---

## Tech Stack

| Component | Technology |
|---|---|
| Risk Model | LightGBM |
| Agent Orchestration | LangGraph |
| LLM | Groq (Qwen3.8-27b) |
| Dashboard | Streamlit |
| Audit Log | SQLite |
| Payment Rails | Razorpay Test Mode API |
| Language | Python 3.14 |

---

## Project Structure

```
chargeback-evidence-responder/
├── src/
│   ├── generate_data.py      # Synthetic dataset generator
│   ├── train_model.py        # LightGBM risk scorer training
│   ├── decision.py           # Cost-aware EV decision layer
│   ├── evidence_writer.py    # Evidence gatherer + LLM packet writer
│   ├── pipeline.py           # LangGraph orchestration + audit log
│   └── app.py                # Streamlit dashboard
├── models/
│   └── risk_model.pkl        # Trained LightGBM model
├── data/
│   ├── train.csv             # Training split (400 cases)
│   └── test.csv              # Held-out test split (100 cases)
├── .streamlit/
│   └── config.toml           # UI theme
└── requirements.txt
```

---

## Run Locally

```bash
git clone https://github.com/ArnavYadav0047/chargeback-evidence-responder
cd chargeback-evidence-responder
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

Add your keys to .env:

```
RAZORPAY_KEY_ID=your_key
RAZORPAY_KEY_SECRET=your_secret
GROQ_API_KEY=your_key
```

Then run:

```bash
PYTHONPATH=. streamlit run src/app.py
```

---

## Known Limitations

- Audit log uses SQLite and does not persist across Streamlit Cloud restarts. Production would use PostgreSQL.
- Synthetic training data — real-world accuracy would require retraining on actual Razorpay dispute data.
- LLM evidence packets are grounded in provided fields only — no external data fetching.

---

## Builder

**Arnav Yadav**
B.Tech Computer Science and Design, RGIPT Amethi
Research Intern, IIT Delhi SPRING Lab (Adversarial ML / IoT Security)