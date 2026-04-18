"""
Opens a browser for Voice123 login and saves the auth token.
Run this once, or whenever the scraper says the token has expired.

Usage: python3 auth.py
"""
import asyncio
import json
from pathlib import Path
from playwright.async_api import async_playwright

LOCALSTORAGE_PATH = Path(__file__).parent / '.v123_localstorage.json'
SESSION_PATH      = Path(__file__).parent / '.v123_session.json'

async def main():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=False)
        context = await browser.new_context(viewport={'width': 1280, 'height': 900})
        page    = await context.new_page()

        await page.goto('https://voice123.com', wait_until='domcontentloaded')
        print("Log in to Voice123 in the browser, then press Enter here.")
        input()

        # Save cookies and localStorage
        SESSION_PATH.write_text(json.dumps(await context.cookies()))
        raw = await page.evaluate(
            "() => JSON.stringify(Object.fromEntries(Object.entries(window.localStorage)))"
        )
        LOCALSTORAGE_PATH.write_text(raw)

        storage = json.loads(raw)
        if storage.get('auth_token'):
            print("Auth token saved.")
        else:
            print("WARNING: No auth_token found in localStorage — may not be logged in.")

        await browser.close()

asyncio.run(main())
