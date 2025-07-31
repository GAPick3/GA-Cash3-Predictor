## 📁 Project Structure

# GA-Cash3-Predictor 🎲

A lightweight Flask dashboard that ingests Georgia Cash 3 historical draw data, shows the latest draw, and summarizes frequency-based triplets (most/least common and digit frequencies). Designed for transparency—draws are independent; historical data is descriptive, not predictive.

## 📌 Features

- Loads cleaned Cash 3 results CSV (`Date`, `Draw`, `DrawTime`, `Digit1`, `Digit2`, `Digit3`)
- Displays latest draw, scheduled time, and past combination statistics
- Provides JSON endpoints for programmatic access
- Automated updates 30 minutes after each draw via GitHub Actions
- Disclaimer clarifying independence of draws

## Required Files (repo layout)
