from flask import Flask, render_template
import pandas as pd
from predictor import predict_next_numbers

app = Flask(__name__)

@app.route('/')
def index():
    df = pd.read_csv('data/ga_cash3_history.csv')

    # Ensure Date column is treated properly
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.sort_values(by='Date', ascending=False)

    latest_draw = df.iloc[0]
    draw_date = latest_draw['Date'].strftime('%Y-%m-%d')
    draw_time = latest_draw['DrawTime']
    winning_numbers = f"{int(latest_draw['Digit1'])} {int(latest_draw['Digit2'])} {int(latest_draw['Digit3'])}"

    prediction = predict_next_numbers(df)

    return render_template('index.html',
                           draw_date=draw_date,
                           draw_time=draw_time,
                           winning_numbers=winning_numbers,
                           prediction=prediction)

if __name__ == '__main__':
    app.run(debug=True)
