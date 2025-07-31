from flask import Flask, render_template, request
import pandas as pd
from predictions import predict_next_numbers, evaluate_accuracy
import os

app = Flask(__name__)

@app.route("/")
def index():
    try:
        # === Load Data ===
        data_path = "data/ga_cash3_history_cleaned.csv"
        if not os.path.exists(data_path):
            return "CSV file not found.", 500

        df = pd.read_csv(data_path, parse_dates=["Date"])
        df = df.sort_values("Date").reset_index(drop=True)

        # === Prediction Logic ===
        prediction = predict_next_numbers(df)
        last_actual_row = df.iloc[-1]
        last_actual = [int(last_actual_row['Digit1']), int(last_actual_row['Digit2']), int(last_actual_row['Digit3'])]

        # === Compare with Last Draw ===
        if prediction == last_actual:
            match_type = "Exact"
        elif sorted(prediction) == sorted(last_actual):
            match_type = "AnyOrder"
        else:
            match_type = "Miss"

        # === Dropdown filter: default to 30 ===
        filter_val = request.args.get("filter", default="30")
        try:
            filter_val = int(filter_val)
        except ValueError:
            filter_val = 30

        accuracy_data = evaluate_accuracy(df, filter_val)

        return render_template("index.html",
                               prediction=prediction,
                               last_actual=last_actual,
                               match_type=match_type,
                               accuracy_data=accuracy_data,
                               total_draws=filter_val,
                               selected_filter=filter_val)

    except Exception as e:
        import traceback
        return f"<pre>{traceback.format_exc()}</pre>", 500


if __name__ == "__main__":
    app.run(debug=True)
