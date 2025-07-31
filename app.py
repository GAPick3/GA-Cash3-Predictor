from flask import Flask, render_template
import pandas as pd
import os

app = Flask(__name__)

@app.route("/")
def index():
    data_path = "data/ga_cash3_history_cleaned.csv"

    df = pd.read_csv(
        data_path,
        parse_dates=["Date"],
        date_format="%m/%d/%y"  # ✅ NEW way using date_format
    )

    df.sort_values("Date", ascending=False, inplace=True)
    latest_result = df.iloc[0]

    # Reconstruct full number
    latest_number = f"{int(latest_result['Digit1'])}{int(latest_result['Digit2'])}{int(latest_result['Digit3'])}"

    return render_template(
        "index.html",
        latest_date=latest_result["Date"].strftime("%B %d, %Y"),
        latest_number=latest_number,
        draw_time=latest_result["DrawTime"]
    )

if __name__ == "__main__":
    app.run(debug=True)
