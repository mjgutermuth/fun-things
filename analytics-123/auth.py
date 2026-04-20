"""
Authenticates with Voice123 via the OpenID Connect password grant and saves
the token to .v123_localstorage.json for use by scraper.py.

Usage: python3 auth.py
"""
import json
import urllib.parse
import urllib.request
import urllib.error
from pathlib import Path

LOCALSTORAGE_PATH = Path(__file__).parent / '.v123_localstorage.json'
CONFIG_PATH       = Path(__file__).parent / 'config.json'

ACCOUNTS_URL = 'https://accounts.voice123.com/openid/token'
OAUTH_CLIENT = '450535'


def main():
    config   = json.loads(CONFIG_PATH.read_text())
    email    = config['voice123']['email']
    password = config['voice123']['password']

    print("[auth] Requesting token...")
    data = urllib.parse.urlencode({
        'grant_type': 'password',
        'username':   email,
        'password':   password,
        'client_id':  OAUTH_CLIENT,
    }).encode()
    req = urllib.request.Request(
        ACCOUNTS_URL, data=data,
        headers={'Content-Type': 'application/x-www-form-urlencoded'}
    )
    try:
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"[auth] Failed ({e.code}): {body}")
        return

    access_token  = result.get('access_token')
    refresh_token = result.get('refresh_token')

    if not access_token:
        print(f"[auth] No access_token in response: {result}")
        return

    storage = {'auth_token': access_token}
    if refresh_token:
        storage['rt'] = refresh_token
    LOCALSTORAGE_PATH.write_text(json.dumps(storage))
    print("[auth] Token saved.")


if __name__ == '__main__':
    main()
