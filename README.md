# GA Cash3 Predictor

## Overview
Automated pipeline to ingest Georgia Cash 3 results, fallback to PDF if needed, compute summaries, and produce heuristic predictions.

## Key components
- `prepare_data.py`: orchestrates fetching (HTML snapshot → PDF fallback), normalization, history merge, and summary generation.
- `fetch_html_snapshot.py`: (optional) renders the live site to produce `data/latest.htm` when direct scraping fails.
- `predictor.py`: scores and suggests likely triplets based on frequency and recency.
- `templates/index.html`: frontend displaying latest draw, predictions, and summaries.

## Automation
GitHub Actions workflow (`.github/workflows/update.yml`) runs 30 minutes after each draw to refresh the data.

## Local setup
```sh
python -m pip install -r requirements.txt
# Optional: install Playwright (if using snapshot)
playwright install

python prepare_data.py  # populates data/ga_cash3_history.csv and data/summary.json
python app.py           # runs Flask app locally
