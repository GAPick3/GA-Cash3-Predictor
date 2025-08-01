# fetch_html_snapshot.py
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright
from config import LATEST_HTML

URL = "https://www.lotterypost.com/results/georgia/cash-3"  # or official page

async def snapshot():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto(URL, wait_until="networkidle")
        # Optional: wait for expected DOM element with JS rendered results
        await page.wait_for_timeout(2000)  # small delay to ensure JS runs
        content = await page.content()
        LATEST_HTML.parent.mkdir(parents=True, exist_ok=True)
        LATEST_HTML.write_text(content, encoding="utf-8")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(snapshot())
