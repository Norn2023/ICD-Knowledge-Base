"""HTTP server for DIP web app"""
from http.server import HTTPServer, SimpleHTTPRequestHandler
import os, gzip
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
        # Serve JSON files, prefer gzipped version
        if self.path.endswith('.json'):
            raw = os.path.join(DIR, self.path.lstrip('/'))
            # Skip gzip content-encoding for large files that clients may not decode
            skip_encoding = ('drug_audit_index.json' in raw or 'pricing_guide_tech.json' in raw)
            gzpath = raw + '.gz'
            if os.path.exists(gzpath) and not skip_encoding:
                with open(gzpath, 'rb') as f:
                    data = f.read()
                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.send_header('Content-Encoding', 'gzip')
                self.send_header('Content-Length', str(len(data)))
                self.end_headers()
                self.wfile.write(data)
                return
            elif os.path.exists(raw):
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
