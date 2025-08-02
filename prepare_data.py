from datetime import datetime, timezone
import json

def compute_simple_insights(df, window=100):
    # === placeholder: adapt to your real logic ===
    # Example structure expected by template: has .common and .uncommon with Digit1/2/3
    # This is dummy; replace with your actual computation.
    return {
        "common": {"Digit1": 1, "Digit2": 2, "Digit3": 3},
        "uncommon": {"Digit1": 7, "Digit2": 8, "Digit3": 9},
    }

def build_summary(df):
    insights = compute_simple_insights(df, window=100)
    summary = {
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "total_draws": int(len(df)),
        "latest_draw": {},  # fill if you have logic to extract latest draw
        "predictions": insights,
        "simple_insights": insights,  # alias for backwards compatibility
    }

    # Optionally set latest_draw if you have the last row
    if not df.empty:
        latest = df.iloc[-1].to_dict()
        summary["latest_draw"] = latest

    with open("data/summary.json", "w") as f:
        json.dump(summary, f, indent=2)
    print(f"✅ Summary written to data/summary.json")
