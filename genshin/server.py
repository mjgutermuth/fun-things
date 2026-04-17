#!/usr/bin/env python3
"""Local dev server — serves static files and opens the browser."""
import http.server
import os
import threading
import webbrowser
from pathlib import Path

PORT = 5001
os.chdir(Path(__file__).parent)


class Handler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


if __name__ == '__main__':
    httpd = http.server.HTTPServer(('', PORT), Handler)
    threading.Timer(0.5, lambda: webbrowser.open(f'http://localhost:{PORT}')).start()
    print(f'Serving at http://localhost:{PORT}  (Ctrl+C to stop)')
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
