from flask import Flask, render_template
import pandas as pd
import matplotlib.pyplot as plt
import os

app = Flask(__name__)

@app.route('/')
def home():
    try:
        # Load cleaned data
        data = pd.read_csv('data/ga_cash3_history_cleaned.csv')
        data = data.dropna(subset=['Digit1', 'Digit2', 'Digit3'])

        # Ensure date is in correct format
        data['Date'] = pd.to_datetime(data['Date'], errors='coerce')
        data = data.sort_values(by='Date', ascending=False)

        # Get latest draw
        latest_draw = data.iloc[0]
        latest_date = latest_draw['Date'].strftime('%Y-%m-%d') if pd.notnull(latest_draw['Date']) else 'Unknown'
        latest_time = latest_draw.get('DrawTime', 'Unknown')
        latest_numbers = [int(latest_draw['Digit1']), int(latest_draw['Digit2']), int(latest_draw['Digit3'])]

        # Get top 10 hot digits
        digits = pd.concat([data['Digit1'], data['Digit2'], data['Digit3']])
        hot_numbers = digits.value_counts().head(10).sort_index()

        # Plot hot number frequency chart
        plt.figure(figsize=(6, 4))
        hot_numbers.sort_values().plot(kind='bar', color='orange')
        plt.title('🔥 Top 10 Hot Numbers')
        plt.xlabel('Number')
        plt.ylabel('Frequency')
        plt.tight_layout()

        # Save chart to static directory
        chart_path = 'static/hot_numbers.png'
        if not os.path.exists('static'):
            os.makedirs('static')
        plt.savefig(chart_path)
        plt.close()

        return render_template(
            'index.html',
            latest_date=latest_date,
            latest_time=latest_time,
            latest_numbers=latest_numbers,
            chart_path=chart_path
        )

    except Exception as e:
        return f"<h2>Error loading page: {str(e)}</h2>"

if __name__ == '__main__':
    app.run(debug=True)
