# pdf_parser.py

import pdfplumber
import pandas as pd
import os

def extract_cash3_from_pdf(pdf_path):
    results = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            for line in text.splitlines():
                parts = line.strip().split()
                # Customize this if your format is different
                if len(parts) >= 5 and parts[1].lower() in ['mid', 'eve', 'night']:
                    date = parts[0]
                    draw = parts[1].lower()
                    nums = parts[2:5]
                    results.append([date, draw] + nums)
    return results

def save_to_csv(data, filename="data/ga_cash3_history.csv"):
    os.makedirs("data", exist_ok=True)
    df = pd.DataFrame(data, columns=["Date", "Draw", "Number1", "Number2", "Number3"])
    df.to_csv(filename, index=False)
    print(f"✅ Saved {len(df)} rows to {filename}")

def main():
    pdf_path = "cash3_results.pdf"
    print(f"🔍 Extracting from {pdf_path}")
    data = extract_cash3_from_pdf(pdf_path)
    save_to_csv(data)

if __name__ == "__main__":
    main()
