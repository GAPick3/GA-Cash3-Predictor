# app.py

from flask import Flask, render_template
import pandas as pd
from predictor import predict_next_numbers

app = Flask(__name__)

@app.route("/")
def index():
    data_path = "data/ga_cash3_history_cleaned.csv"

    # Load CSV and manually parse date with 2-digit year format
    try:
        df = pd.read_csv(data_path, dtype={"Date": str})
        df["Date"] = pd.to_datetime(df["Date"], format="%m/%d/%y", errors="raise")
    except Exception as e:
        return f"Error loading data: {e}", 500

    # Sort and get the latest result
    df = df.sort_values(by="Date", ascending=False)
    latest_result = df.iloc[0]

    # Predict next numbers
    prediction = predict_next_numbers(df)

    return render_template(
        "index.html",
        latest_date=latest_result["Date"].strftime("%B %d, %Y"),
        winning_numbers=f"{latest_result['Digit1']}{latest_result['Digit2']}{latest_result['Digit3']}",
        draw_time=latest_result["DrawTime"],
        prediction=prediction
    )

if __name__ == "__main__":
    app.run(debug=True)
