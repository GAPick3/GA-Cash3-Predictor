# prepare_data.py
import json
import time
from datetime import datetime
from collections import Counter, defaultdict
import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
import shutil
import tempfile
from pathlib import Path

from config import HISTORY_CSV, LATEST_HTML, LATEST_PDF, SUMMARY_JSON, PDF_URL

# Utility: atomic CSV write
def atomic_write_csv(df: pd.DataFrame, path: Path):
    tmp = Path(f"{path}.tmp")
    df.to_csv(tmp, index=False)
    tmp.replace(path)

def load_history():
    if HISTORY_CSV.exists():
        df = pd.read_csv(HISTORY_CSV, parse_dates=["Date"], dtype={"Draw": str})
        df = df.sort_values(["Date", "Draw"], ascending=[False, False])
        df = df.drop_duplicates(subset=["Date", "Draw"], keep="first")
        return df
    else:
        return pd.DataFrame(columns=["Date", "Draw", "DrawTime", "Digit1", "Digit2", "Digit3"])

def save_history(df: pd.DataFrame):
    atomic_write_csv(df, HISTORY_CSV)

def extract_from_html(html_path: Path):
    if not html_path.exists():
        return []
    with open(html_path, 'r', encoding='utf-8', errors='ignore') as f:
        soup = BeautifulSoup(f, 'html.parser')

    draws = []

    # Heuristic 1: embedded JSON
    for script in soup.find_all("script"):
        text = script.string or ""
        if not text:
            continue
        # Attempt to find JSON objects
        try:
            # loose heuristic: extract {...} blocks with digits
            for match in re.findall(r'\{.*?\}', text, flags=re.DOTALL):
                try:
                    obj = json.loads(match)
                except json.JSONDecodeError:
                    continue
                # Adapt this depending on the real structure; example placeholder:
                if isinstance(obj, dict):
                    # If structure contains results
                    if 'results' in obj:
                        for item in obj['results']:
                            date_str = item.get("date") or item.get("draw_date")
                            draw_name = item.get("draw") or item.get("name")
                            numbers = item.get("numbers") or item.get("winning")  # array
                            if date_str and draw_name and numbers and len(numbers) >= 3:
                                try:
                                    date = datetime.fromisoformat(date_str).date()
                                except Exception:
                                    continue
                                digits = [int(n) for n in numbers[:3]]
                                draws.append({
                                    "Date": date.isoformat(),
                                    "Draw": draw_name,
                                    "DrawTime": "",  # filled later or via logic
                                    "Digit1": digits[0],
                                    "Digit2": digits[1],
                                    "Digit3": digits[2],
                                })
        except Exception:
            continue

    # Heuristic 2: table fallback
    if not draws:
        for row in soup.select("table tr"):
            cols = [c.get_text(strip=True) for c in row.find_all(["td", "th"])]
            if len(cols) >= 3 and re.match(r'\d{1,2}/\d{1,2}/\d{4}', cols[0]):
                try:
                    date = datetime.strptime(cols[0], "%m/%d/%Y").date()
                except ValueError:
                    continue
                draw_label = cols[1]
                # numbers might be separated by spaces or punctuation
                nums = re.sub(r'\D', '', cols[2])
                if len(nums) == 3:
                    digits = [int(n) for n in nums]
                    draws.append({
                        "Date": date.isoformat(),
                        "Draw": draw_label,
                        "DrawTime": "",  # fill later
                        "Digit1": digits[0],
                        "Digit2": digits[1],
                        "Digit3": digits[2],
                    })
    return normalize_draws(draws)

def download_pdf():
    headers = {"User-Agent": "Mozilla/5.0 (compatible; GA-Cash3-Predictor/1.0)"}
    backoff = 1
    for attempt in range(4):
        try:
            resp = requests.get(PDF_URL, headers=headers, timeout=10)
            resp.raise_for_status()
            content = resp.content
            if not content.startswith(b"%PDF"):
                raise ValueError("Downloaded content is not a PDF")
            with open(LATEST_PDF, "wb") as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"[prepare_data] PDF download attempt {attempt+1} failed: {e}")
            time.sleep(backoff)
            backoff *= 2
    return False

def parse_pdf(pdf_path: Path):
    import pdfplumber  # delayed import
    if not pdf_path.exists():
        return []
    draws = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            # naive: scan all pages for table with Cash 3
            for page in pdf.pages:
                tables = page.extract_tables()
                for table in tables:
                    # attempt to identify header row with Date / Draw / Numbers
                    header = [h.lower() if h else "" for h in table[0]]
                    if any("date" in h for h in header) and any("number" in h or "winning" in h for h in header):
                        # find indices
                        try:
                            date_idx = next(i for i, h in enumerate(header) if "date" in h)
                        except StopIteration:
                            continue
                        draw_idx = None
                        for i, h in enumerate(header):
                            if "draw" in h or "time" in h:
                                draw_idx = i
                                break
                        numbers_idx = next((i for i, h in enumerate(header) if "number" in h or "winning" in h), None)
                        body = table[1:]
                        for row in body:
                            # safety: row may be shorter
                            if date_idx >= len(row) or numbers_idx is None or numbers_idx >= len(row):
                                continue
                            raw_date = row[date_idx]
                            raw_draw = row[draw_idx] if draw_idx is not None and draw_idx < len(row) else ""
                            raw_numbers = row[numbers_idx]
                            if not raw_date or not raw_numbers:
                                continue
                            try:
                                date = datetime.strptime(raw_date.strip(), "%m/%d/%Y").date()
                            except Exception:
                                continue
                            nums = re.sub(r'\D', '', raw_numbers)
                            if len(nums) != 3:
                                continue
                            digits = [int(n) for n in nums]
                            draws.append({
                                "Date": date.isoformat(),
                                "Draw": raw_draw.strip(),
                                "DrawTime": "",
                                "Digit1": digits[0],
                                "Digit2": digits[1],
                                "Digit3": digits[2],
                            })
    except Exception as e:
        print(f"[prepare_data] PDF parsing error: {e}")
    return normalize_draws(draws)

def normalize_draws(raw_list):
    """
    Accept list of dicts with keys possibly varying; enforce schema and fill DrawTime if missing.
    """
    cleaned = []
    for r in raw_list:
        try:
            date = r.get("Date")
            if isinstance(date, str):
                # accept ISO or m/d/Y
                try:
                    dt = datetime.fromisoformat(date).date()
                except ValueError:
                    dt = datetime.strptime(date, "%m/%d/%Y").date()
            elif isinstance(date, datetime):
                dt = date.date()
            else:
                continue
            draw = r.get("Draw", "").strip()
            # Normalize draw label to one of expected
            if draw.lower().startswith("mid"):
                draw_norm = "Midday"
            elif draw.lower().startswith("even"):
                draw_norm = "Evening"
            elif draw.lower().startswith("night"):
                draw_norm = "Night"
            else:
                draw_norm = draw or "Unknown"

            d1 = int(r.get("Digit1") or (str(r.get("Numbers") or "")[0] if r.get("Numbers") else 0))
            d2 = int(r.get("Digit2") or (str(r.get("Numbers") or "")[1] if r.get("Numbers") else 0))
            d3 = int(r.get("Digit3") or (str(r.get("Numbers") or "")[2] if r.get("Numbers") else 0))

            # Infer DrawTime from draw name if blank
            draw_time = r.get("DrawTime") or ""
            if not draw_time:
                from config import DRAW_TIMES
                draw_time = DRAW_TIMES.get(draw_norm, "")

            cleaned.append({
                "Date": dt.isoformat(),
                "Draw": draw_norm,
                "DrawTime": draw_time,
                "Digit1": d1,
                "Digit2": d2,
                "Digit3": d3,
            })
        except Exception:
            continue
    # Deduplicate within the new batch
    seen = set()
    result = []
    for item in cleaned:
        key = (item["Date"], item["Draw"])
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result

def merge_and_update():
    history = load_history()
    existing_keys = set(history[["Date", "Draw"]].apply(lambda row: (row["Date"].date() if hasattr(row["Date"], "date") else (pd.to_datetime(row["Date"]).date() if pd.notna(row["Date"]) else None), row["Draw"]), axis=1))

    # Try HTML source first
    new_draws = extract_from_html(LATEST_HTML)
    source_used = None
    if new_draws:
        source_used = "html"
    else:
        # Fallback to PDF
        if download_pdf():
            new_draws = parse_pdf(LATEST_PDF)
            source_used = "pdf"
        else:
            source_used = "none"

    if not new_draws:
        print("[prepare_data] No new draws fetched from any source.")
        return history, 0, source_used

    # Convert to DataFrame
    df_new = pd.DataFrame(new_draws)
    # Parse Date column to datetime
    df_new["Date"] = pd.to_datetime(df_new["Date"])
    # Filter out already present
    def key_tuple(row):
        return (row["Date"].date(), row["Draw"])
    added_rows = []
    for _, row in df_new.iterrows():
        key = (row["Date"].date(), row["Draw"])
        if key not in existing_keys:
            added_rows.append(row)

    if not added_rows:
        print("[prepare_data] No new unique draws to add.")
        return history, 0, source_used

    df_added = pd.DataFrame(added_rows)
    updated = pd.concat([df_added, history], ignore_index=True)
    updated["Date"] = pd.to_datetime(updated["Date"])
    updated = updated.sort_values(["Date", "Draw"], ascending=[False, False])
    updated = updated.drop_duplicates(subset=["Date", "Draw"], keep="first")
    save_history(updated)
    added_count = len(df_added)
    print(f"[prepare_data] Source used: {source_used}, new draws added: {added_count}")
    return updated, added_count, source_used

def compute_summary(df: pd.DataFrame):
    summary = {}
    df = df.copy()
    df["Triplet"] = df.apply(lambda r: f"{int(r['Digit1'])}{int(r['Digit2'])}{int(r['Digit3'])}", axis=1)

    # Frequency of digits by position
    for pos in ["Digit1", "Digit2", "Digit3"]:
        counts = df[pos].value_counts().to_dict()
        summary[f"{pos}_frequency"] = counts

    # Most common triplets
    triplet_counts = df["Triplet"].value_counts()
    summary["top_triplets"] = triplet_counts.head(5).to_dict()

    # Last seen of each digit
    last_seen = {}
    for pos in ["Digit1", "Digit2", "Digit3"]:
        last_seen[pos] = {}
        for digit in range(10):
            mask = df[df[pos] == digit]
            if not mask.empty:
                last_date = mask.iloc[0]["Date"]
                last_seen[pos][digit] = last_date.strftime("%Y-%m-%d")
            else:
                last_seen[pos][digit] = None
    summary["last_seen"] = last_seen

    # Hot/cold: define hot as top 3 freq in each position
    summary["hot_digits"] = {
        pos: [int(d) for d in df[pos].value_counts().head(3).index.tolist()]
        for pos in ["Digit1", "Digit2", "Digit3"]
    }
    # Cold as bottom 3 (that have appeared at least once)
    summary["cold_digits"] = {}
    for pos in ["Digit1", "Digit2", "Digit3"]:
        vc = df[pos].value_counts()
        bottom = [int(d) for d in vc.tail(3).index.tolist()] if len(vc) >= 3 else [int(d) for d in vc.index.tolist()]
        summary["cold_digits"][pos] = bottom

    # Total draws
    summary["total_draws"] = len(df)
    # Most recent draw
    latest = df.iloc[0]
    summary["latest"] = {
        "Date": latest["Date"].strftime("%Y-%m-%d"),
        "Draw": latest["Draw"],
        "Triplet": latest["Triplet"],
        "DrawTime": latest.get("DrawTime", "")
    }

    return summary

def save_summary(summary: dict):
    with open(SUMMARY_JSON, "w") as f:
        json.dump(summary, f, default=str, indent=2)

def main():
    updated_history, added_count, source = merge_and_update()
    summary = compute_summary(updated_history)
    save_summary(summary)

if __name__ == "__main__":
    main()
