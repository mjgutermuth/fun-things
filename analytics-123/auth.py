"""
Saves a Voice123 auth token by reading it from your browser's localStorage.
Works on any machine — no display or Playwright needed.

From your Mac (clipboard → server in one step):
  1. Open https://voice123.com in any browser and log in
  2. Open the console (F12 → Console tab)
  3. Run: copy(JSON.stringify(Object.fromEntries(Object.entries(localStorage))))
  4. On your Mac terminal:
       pbpaste | ssh YOUR_SERVER 'python3 ~/workspace/fun-things/analytics-123/auth.py'

Or write the file directly without SSH:
  pbpaste | python3 auth.py

Interactive fallback (paste may be truncated by terminal on long JSON):
  python3 auth.py
  (paste, then Ctrl+D)
"""
import json
import sys
from pathlib import Path

LOCALSTORAGE_PATH = Path(__file__).parent / '.v123_localstorage.json'

def main():
    if sys.stdin.isatty():
        print("1. Open https://voice123.com in any browser and log in")
        print("2. Open the console (F12 → Console tab)")
        print("3. Run this command and copy the output:")
        print()
        print("   copy(JSON.stringify(Object.fromEntries(Object.entries(localStorage))))")
        print()
        print("Paste here, then press Ctrl+D:")
        print("(If paste gets truncated, use: pbpaste | python3 auth.py  from your Mac)")
        print()

    raw = sys.stdin.read().strip()
    if not raw:
        sys.exit("Nothing received. Exiting.")

    try:
        storage = json.loads(raw)
    except json.JSONDecodeError as e:
        sys.exit(f"Invalid JSON: {e}")

    if not storage.get('auth_token'):
        sys.exit("No auth_token found — make sure you're logged in before copying.")

    LOCALSTORAGE_PATH.write_text(json.dumps(storage))
    print("Auth token saved.")

if __name__ == '__main__':
    main()
