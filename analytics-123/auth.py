"""
Saves a Voice123 auth token by reading it from your browser's localStorage.
Works on any machine — no display or Playwright needed.

Steps:
  1. Open https://voice123.com in any browser and log in
  2. Open the browser console (F12 → Console)
  3. Run: copy(JSON.stringify(Object.fromEntries(Object.entries(localStorage))))
  4. Run this script and paste when prompted

Usage: python3 auth.py
"""
import json
import sys
from pathlib import Path

LOCALSTORAGE_PATH = Path(__file__).parent / '.v123_localstorage.json'

def main():
    print("1. Open https://voice123.com in any browser and log in")
    print("2. Open the console (F12 → Console tab)")
    print("3. Run this command and copy the output:")
    print()
    print("   copy(JSON.stringify(Object.fromEntries(Object.entries(localStorage))))")
    print()
    print("Paste here and press Enter (then Ctrl+D on a blank line if needed):")

    lines = []
    try:
        while True:
            line = input()
            lines.append(line)
    except EOFError:
        pass

    raw = '\n'.join(lines).strip()
    if not raw:
        sys.exit("Nothing pasted. Exiting.")

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
