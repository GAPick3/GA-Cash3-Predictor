import fitz  # PyMuPDF
import csv
import os
from datetime import datetime

def extract_cash3_from_pdf(pdf_path, output_csv):
    doc = fitz.open(pdf_path)
    results = []

    for page in doc:
        text = page.get_text()
        lines = text.split('\n')
        for line in lines:
            if "Cash 3 Midday" in line or "Cash 3 Evening" in line or "Cash 3 Night" in line:
                parts = line.split()
                try:
                    # Expecting: Date | Game | Numbers
                    date = parts[0]
                    draw_time = parts[2].lower()
                    numbers = parts[-3:]
                    datetime.strptime(date, "%m/%d/%Y")  # validate
                    if len(numbers) == 3:
                        results.append([date, draw_time] + numbers)
                except:
                    continue

    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
    with open(output_csv, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Date", "Draw", "Number1", "Number2", "Number3"])
        writer.writerows(results)
    print(f"✅ Extracted {len(results)} records to {output_csv}")

if __name__ == "__main__":
    extract_cash3_from_pdf("data/GA_Lottery_WinningNumbers.pdf", "data/ga_cash3_history.csv")
