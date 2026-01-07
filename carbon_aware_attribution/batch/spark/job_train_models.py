import pandas as pd
from sklearn.linear_model import Ridge
import joblib

def main():
    df = pd.read_parquet("/app/data/daily_campaign_features.parquet")
    df["conv_per_usd"] = df["conversions"] / (df["cost_usd"] + 1e-6)

    X = df[["cost_usd", "clicks"]].fillna(0.0).values
    y = df["conv_per_usd"].fillna(0.0).values

    m = Ridge(alpha=1.0)
    m.fit(X, y)

    joblib.dump(m, "/app/data/conv_model.joblib")
    print("saved /app/data/conv_model.joblib")

if __name__ == "__main__":
    main()