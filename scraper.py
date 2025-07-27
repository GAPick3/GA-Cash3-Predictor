def fetch_data():
    url = "https://www.lotterypost.com/results/georgia/cash-3"
    print(f"🔎 Scraping: {url}")
    
    try:
        resp = requests.get(url, headers={"User-Agent":"Mozilla/5.0"})
        resp.raise_for_status()
    except Exception as e:
        print("❌ Failed:", e)
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    today = datetime.now().date()
    cutoff = today - timedelta(days=3 * 365)

    data = []

    for row in soup.select("table.results tbody tr"):
        try:
            cols = row.find_all("td")
            if len(cols) < 3:
                continue

            date_text = cols[0].text.strip()
            draw_date = datetime.strptime(date_text, "%m/%d/%Y").date()
            if draw_date < cutoff:
                continue

            draw_time = cols[1].text.strip().lower()
            numbers = [n.strip() for n in cols[2].text.strip().split() if n.strip().isdigit()]
            if len(numbers) == 3:
                data.append([draw_date.isoformat(), draw_time] + numbers)
        except Exception as e:
            print(f"⚠️ Skipping row due to error: {e}")
            continue

    return data
