def scrape_url(draw_type, url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/115.0.0.0 Safari/537.36"
    }
    res = requests.get(url, headers=headers)
    res.raise_for_status()
    soup = BeautifulSoup(res.text, "html.parser")

    table = soup.find("table", {"class": "archive-table"})
    rows = table.find_all("tr")[1:]  # skip header
    records = []

    for row in rows:
        cols = row.find_all("td")
        if len(cols) < 2:
            continue
        date_str = cols[0].text.strip()
        numbers = cols[1].text.strip().split("–")  # en-dash
        if len(numbers) != 3:
            continue
        try:
            dt = datetime.strptime(date_str, "%m/%d/%Y").date()
            d1, d2, d3 = [int(n.strip()) for n in numbers]
            records.append((dt.isoformat(), draw_type, d1, d2, d3))
        except Exception:
            continue

    return records
