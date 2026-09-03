import pandas as pd
import lightgbm as lgb
import pickle
import os
from sklearn.metrics import classification_report, confusion_matrix

FEATURES = [
    "amount", "delivery_confirmed", "ip_location_match",
    "device_fingerprint_match", "customer_order_history",
    "days_to_dispute", "chargeback_fee", "cost_of_goods"
]

def train():
    train_df = pd.read_csv("data/train.csv")
    test_df = pd.read_csv("data/test.csv")

    X_train, y_train = train_df[FEATURES], train_df["label"]
    X_test, y_test = test_df[FEATURES], test_df["label"]

    model = lgb.LGBMClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    # Evaluate on held-out test set
    y_pred = model.predict(X_test)
    print("\n--- HELD-OUT TEST SET RESULTS ---")
    print(classification_report(y_test, y_pred, target_names=["Legit", "Fraud"]))
    print("Confusion Matrix:")
    print(confusion_matrix(y_test, y_pred))

    # Save model
    os.makedirs("models", exist_ok=True)
    with open("models/risk_model.pkl", "wb") as f:
        pickle.dump(model, f)
    print("\nModel saved to models/risk_model.pkl")

if __name__ == "__main__":
    train()