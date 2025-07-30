from flask import Flask, render_template
import pandas as pd
from predictor import predict_next_numbers

app = Flask(__name__)

@app.route('/')
def index():
    df = pd.read_csv('data/ga_cash3_history.csv')
    latest_draw = df.iloc[0]  # most recent row
    draw_date = latest_draw['Draw Date']
    draw_time = latest_draw['Draw Time']
    winning_number = f"{int(latest_draw['Digit1'])}{int(latest_draw['Digit2'])}{int(latest_draw['Digit3'])}"
    predictions = predict_next_numbers(df)

    return render_template('index.html',
                           draw_date=draw_date,
                           draw_time=draw_time,
                           winning_number=winning_number,
                           predictions=predictions)

if __name__ == '__main__':
    app.run(debug=True)
