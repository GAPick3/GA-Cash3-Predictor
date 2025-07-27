import pdfplumber
import pandas as pd

pdf_path = "data/GA_Lottery_WinningNumbers (1).PDF"
output_csv = "data/ga_cash3_history.csv"

data = []

with pdfplumber.open(pdf_path) as pdf:
    for page in pdf.pages:
        text = page.extract_text()
        lines = text.split("\n")

        for line in lines:
            # Skip headers
            if line.startswith("Date") or line.startswith("Cash 3"):
                continue
            parts = line.strip().split()
            if len(parts) >= 6 and "/" in parts[0]:
                try:
                    date = parts[0]
                    draw = parts[1].lower()
                    nums = parts[2:5]
                    if all(n.isdigit() for n in nums):
                        data.append([date, draw] + nums)
                except Exception as e:
                    print("⚠️ Failed to parse line:", line)

df = pd.DataFrame(data, columns=["Date", "Draw", "Number1", "Number2", "Number3"])
df.to_csv(output_csv, index=False)
print(f"✅ Extracted {len(df)} records to {output_csv}")
