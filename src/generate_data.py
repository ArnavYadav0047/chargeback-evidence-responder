import pandas as pd
import numpy as np
import random
import os

np.random.seed(42)
random.seed(42)

def generate_dataset(n=500):
    records = []
    for i in range(n):
        is_fraud = random.random() < 0.35  # 35% fraudulent chargebacks

        record = {
            "case_id": f"CB_{i:04d}",
            "amount": round(random.uniform(200, 15000), 2),
            "delivery_confirmed": random.random() < (0.2 if is_fraud else 0.85),
            "ip_location_match": random.random() < (0.3 if is_fraud else 0.9),
            "device_fingerprint_match": random.random() < (0.4 if is_fraud else 0.92),
            "customer_order_history": random.randint(0, 2) if is_fraud else random.randint(1, 15),
            "days_to_dispute": random.randint(1, 7) if is_fraud else random.randint(10, 60),
            "payment_method": random.choice(["upi", "card", "netbanking"]),
            "chargeback_fee": 250,
            "cost_of_goods": round(random.uniform(200, 15000), 2),
            "label": 1 if is_fraud else 0  # 1 = fraudulent chargeback
        }
        records.append(record)

    df = pd.DataFrame(records)

    # 80/20 train-test split — never touch test set until final eval
    split = int(0.8 * n)
    os.makedirs("data", exist_ok=True)
    df[:split].to_csv("data/train.csv", index=False)
    df[split:].to_csv("data/test.csv", index=False)
    print(f"Generated {n} records → {split} train, {n-split} test")

if __name__ == "__main__":
    generate_dataset()