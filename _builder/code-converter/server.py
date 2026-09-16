"""HTTP server for ICD coding converter - port 8767"""
import http.server, os, gzip, json

PORT = 8767
BASE = os.path.dirname(os.path.abspath(__file__))

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=BASE, **kwargs)

    def do_GET(self):
        path = self.path.split('?')[0]
        filepath = os.path.join(BASE, path.lstrip('/'))

        # Serve gzipped JSON for large mapping files
        if path.endswith('.json') and os.path.exists(filepath):
            gzpath = filepath + '.gz'
            if os.path.exists(gzpath):
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Encoding', 'gzip')
                self.send_header('Cache-Control', 'public, max-age=86400')
                self.end_headers()
                with open(gzpath, 'rb') as f:
                    self.wfile.write(f.read())
                return
            else:
                # Generate gzip on the fly
                with open(filepath, 'rb') as f:
                    data = f.read()
                gzdata = gzip.compress(data, compresslevel=9)
                with open(gzpath, 'wb') as f:
                    f.write(gzdata)
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Encoding', 'gzip')
                self.send_header('Cache-Control', 'public, max-age=86400')
                self.end_headers()
                self.wfile.write(gzdata)
                return

        return super().do_GET()

    def log_message(self, format, *args):
        pass  # Silent

if __name__ == '__main__':
    # Pre-gzip the mapping files
    for fname in ['icd10_map.json', 'icd9_map.json']:
        fpath = os.path.join(BASE, fname)
        gzpath = fpath + '.gz'
        if os.path.exists(fpath) and not os.path.exists(gzpath):
            print(f'Gzipping {fname}...')
            with open(fpath, 'rb') as f:
                data = f.read()
            with gzip.open(gzpath, 'wb', compresslevel=9) as f:
                f.write(data)

    print(f'Starting ICD coding converter on http://localhost:{PORT}')
    httpd = http.server.HTTPServer(('0.0.0.0', PORT), Handler)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        httpd.server_close()
