"""
Opens a headless browser, logs in to Voice123 using config.json credentials,
and saves the auth token to .v123_localstorage.json.

Run this once, or whenever the scraper says the token has expired.
Usage: python3 auth.py
"""
import asyncio
import json
from pathlib import Path
from playwright.async_api import async_playwright

LOCALSTORAGE_PATH = Path(__file__).parent / '.v123_localstorage.json'
SESSION_PATH      = Path(__file__).parent / '.v123_session.json'
CONFIG_PATH       = Path(__file__).parent / 'config.json'


async def main():
    config = json.loads(CONFIG_PATH.read_text())
    email    = config['voice123']['email']
    password = config['voice123']['password']

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1280, 'height': 900})
        page    = await context.new_page()

        print("[auth] Navigating to Voice123 login...")
        await page.goto('https://voice123.com/login', wait_until='commit', timeout=15000)
        await page.wait_for_timeout(3000)
        print(f"[auth] URL: {page.url}")
        print(f"[auth] Title: {await page.title()}")
        inputs = await page.query_selector_all('input')
        print(f"[auth] Inputs found: {[await i.get_attribute('type') or await i.get_attribute('name') for i in inputs]}")

        await page.fill('input[type="email"], input[name="email"]', email)
        await page.fill('input[type="password"], input[name="password"]', password)
        await page.click('button[type="submit"]')

        print("[auth] Waiting for login to complete...")
        # Wait until auth_token appears in localStorage (up to 30s)
        await page.wait_for_function(
            "() => !!window.localStorage.getItem('auth_token')",
            timeout=30000
        )

        SESSION_PATH.write_text(json.dumps(await context.cookies()))
        raw = await page.evaluate(
            "() => JSON.stringify(Object.fromEntries(Object.entries(window.localStorage)))"
        )
        LOCALSTORAGE_PATH.write_text(raw)

        storage = json.loads(raw)
        if storage.get('auth_token'):
            print("[auth] Auth token saved.")
        else:
            print("[auth] WARNING: No auth_token found — login may have failed.")

        await browser.close()


asyncio.run(main())
