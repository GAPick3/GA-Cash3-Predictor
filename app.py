from flask import Flask, render_template
import pandas as pd
from predictor import predict_next_numbers
from datetime import datetime

app = Flask(__name__)

DATA_FILE = "data/ga_cash3_history.csv"

def load_data():
    df = pd.read_csv(DATA_FILE)
    df['Draw Date'] = pd.to_datetime(df['Draw Date'])
    df.sort_values(by='Draw Date', ascending=False, inplace=True)
    return df

@app.route("/")
def index():
    df = load_data()
    latest_draw = df.iloc[0]
    
    draw_date = latest_draw['Draw Date'].strftime('%Y-%m-%d')
    draw_time = latest_draw['Draw Time']
    winning_number = latest_draw['Winning Numbers']

    predictions = predict_next_numbers(df)

    return render_template(
        "index.html",
        draw_date=draw_date,
        draw_time=draw_time,
        winning_number=winning_number,
        predictions=predictions
    )

if __name__ == "__main__":
    app.run(debug=True)
