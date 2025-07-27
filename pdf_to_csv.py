import fitz  # PyMuPDF
import csv
import os
from datetime import datetime
import sys

def extract_cash3_from_pdf(pdf_path, output_csv):
    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        print(f"Error opening PDF {pdf_path}: {e}")
        return

    results = []
    skipped_lines = []

    for page_num, page in enumerate(doc, 1):
        text = page.get_text()
        lines = text.split('\n')
        for line in lines:
            if "Cash 3 Midday" in line or "Cash 3 Evening" in line or "Cash 3 Night" in line:
                parts = line.split()
                try:
                    # Expecting: Date | Game | Draw | Numbers
                    date = parts[0]
                    draw_time = parts[2].lower()
                    numbers = parts[-3:]
                    # Validate date
                    datetime.strptime(date, "%m/%d/%Y")
                    # Validate numbers (ensure they are digits)
                    if len(numbers) == 3 and all(num.isdigit() for num in numbers):
                        results.append([date, draw_time] + numbers)
                    else:
                        skipped_lines.append((page_num, line))
                except:
                    skipped_lines.append((page_num, line))
                    continue

    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
    
    # Write to CSV
    try:
        with open(output_csv, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Date", "Draw", "Number1", "Number2", "Number3"])
            writer.writerows(results)
        print(f"✅ Extracted {len(results)} records to {output_csv}")
    except Exception as e:
        print(f"Error writing to CSV {output_csv}: {e}")

    # Report skipped lines for debugging
    if skipped_lines:
        print(f"⚠️ Skipped {len(skipped_lines)} lines due to invalid format:")
        for page_num, line in skipped_lines[:5]:  # Limit to first 5 for brevity
            print(f"  Page {page_num}: {line.strip()}")
        if len(skipped_lines) > 5:
            print(f"  ...and {len(skipped_lines) - 5} more.")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python pdf_to_csv.py <input_pdf> <output_csv>")
        sys.exit(1)
    extract_cash3_from_pdf(sys.argv[1], sys.argv[2])
