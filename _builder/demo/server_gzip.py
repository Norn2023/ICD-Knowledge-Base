"""HTTP server for DIP web app"""
from http.server import HTTPServer, SimpleHTTPRequestHandler
import os
DIR = os.path.dirname(os.path.abspath(__file__))

class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIR, **kwargs)

    def end_headers(self):
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
        super().end_headers()

    def log_message(self, format, *args):
        print(f"[{self.command}] {self.path} -> {args[0]}", flush=True)

    def do_HEAD(self):
        self.do_GET()

    def do_GET(self):
        # Serve JSON files uncompressed
        if self.path.endswith('.json'):
            raw = os.path.join(DIR, self.path.lstrip('/'))
            if os.path.exists(raw):
                with open(raw, 'rb') as f:
                    data = f.read()
                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.send_header('Content-Length', str(len(data)))
                self.end_headers()
                self.wfile.write(data)
                return
        super().do_GET()

port = 8765
print(f'http://localhost:{port}')
HTTPServer(('', port), Handler).serve_forever()
