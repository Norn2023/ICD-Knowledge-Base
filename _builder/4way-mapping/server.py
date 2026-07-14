"""
3-way Mapping Server - Port 8768
上海医疗服务价格项目 → 2023技术规范 → ICD-9-CM-3 编码映射
"""
import http.server
import json
import gzip
import os
import re
import urllib.parse

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
print(f"[DEBUG] server.py loaded from: {__file__}")

DATA_FILE = os.path.join(BASE_DIR, 'data.json.gz')

# Load data on startup
with gzip.open(DATA_FILE, 'rb') as f:
    MAPPING_DATA = json.loads(f.read().decode('utf-8'))

print(f"Loaded mapping data: {len(MAPPING_DATA['cross_refs'])} cross-refs")

# ── Build ICD-10 lookup map from web/ data ──
# Maps procedure name → (icd10_code, icd10_name)
ICD10_MAP = {}
_icd10_src = os.path.join(BASE_DIR, '..', 'web', 'data.json.gz')
if os.path.exists(_icd10_src):
    try:
        with gzip.open(_icd10_src, 'rb') as f:
            web_data = json.loads(f.read().decode('utf-8'))
        icd10_list = web_data.get('icd10', [])
        for entry in icd10_list:
            code = entry.get('code', '')
            name = entry.get('name', '')
            if code and name:
                ICD10_MAP[name] = (code, name)
        print(f"Loaded ICD-10 map: {len(ICD10_MAP)} entries")
    except Exception as e:
        print(f"ICD-10 load skipped: {e}")
MAPPING_DATA['_icd10_map'] = ICD10_MAP

# Instructions data (lazy-loaded)
INSTRUCTIONS_DATA = None

def get_instructions():
    """Load instructions data from _instructions.json"""
    global INSTRUCTIONS_DATA
    if INSTRUCTIONS_DATA is None:
        inst_file = os.path.join(BASE_DIR, '_instructions.json')
        try:
            with open(inst_file, 'r', encoding='utf-8') as f:
                INSTRUCTIONS_DATA = json.load(f)
        except:
            INSTRUCTIONS_DATA = {'categories': {}}
    return INSTRUCTIONS_DATA

# Note files and their keyword triggers
NOTE_REGISTRY = {
    '激光': '激光疗法知识.md',
    'He-Ne': '激光疗法知识.md',
    '氦氖': '激光疗法知识.md',
    '半导体激光': '激光疗法知识.md',
    'LLLT': '激光疗法知识.md',
    '脉冲激光': '激光疗法知识.md',
    '二氧化碳激光': '激光疗法知识.md',
    '激光针': '激光疗法知识.md',
}

# Cache loaded notes
_note_cache = {}

def load_note(filename):
    if filename not in _note_cache:
        filepath = os.path.join(BASE_DIR, filename)
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                _note_cache[filename] = f.read()
        else:
            _note_cache[filename] = ''
    return _note_cache[filename]

def md_to_html(md_text):
    """Simple markdown-to-HTML converter"""
    lines = md_text.split('\n')
    html = []
    in_table = False
    in_code = False
    table_rows = []

    for line in lines:
        # Code blocks
        if line.strip().startswith('```'):
            if in_code:
                html.append('</pre>')
                in_code = False
            else:
                html.append('<pre style="background:#f3f4f6;padding:10px;border-radius:6px;overflow-x:auto;font-size:0.85em;">')
                in_code = True
            continue
        if in_code:
            html.append(line)
            continue

        # Headings
        if line.startswith('# '):
            html.append(f'<h1 style="font-size:1.5em;color:#1a1a2e;border-bottom:2px solid #2563eb;padding-bottom:6px;margin:20px 0 12px;">{line[2:]}</h1>')
            continue
        if line.startswith('## '):
            html.append(f'<h2 style="font-size:1.25em;color:#16213e;border-bottom:1px solid #e5e7eb;padding-bottom:4px;margin:16px 0 10px;">{line[3:]}</h2>')
            continue
        if line.startswith('### '):
            html.append(f'<h3 style="font-size:1.1em;color:#1f2937;margin:14px 0 8px;">{line[4:]}</h3>')
            continue
        if line.startswith('#### '):
            html.append(f'<h4 style="font-size:1em;color:#374151;margin:12px 0 6px;">{line[5:]}</h4>')
            continue

        # Horizontal rule
        if line.strip() == '---':
            html.append('<hr style="border:none;border-top:1px solid #d1d5db;margin:16px 0;">')
            continue

        # Tables
        if '|' in line and line.strip().startswith('|'):
            cells = [c.strip() for c in line.split('|')[1:-1]]
            if all(c.startswith('-') and c.endswith('-') for c in cells):
                # Separator row
                table_rows.append('__SEP__')
            else:
                table_rows.append(cells)
            in_table = True
            continue
        elif in_table:
            in_table = False
            # Render collected table
            if table_rows:
                html.append('<table style="width:100%;border-collapse:collapse;margin:10px 0;font-size:0.85em;">')
                header_done = False
                for row in table_rows:
                    if row == '__SEP__':
                        header_done = True
                        continue
                    tag = 'th' if not header_done else 'td'
                    style_td = 'border:1px solid #d1d5db;padding:6px 10px;text-align:left;'
                    style_th = 'border:1px solid #d1d5db;padding:6px 10px;text-align:left;background:#f8fafc;font-weight:600;'
                    cells_html = ''.join(f'<{tag} style="{style_th if tag=="th" else style_td}">{c}</{tag}>' for c in row)
                    html.append(f'<tr>{cells_html}</tr>')
                    if not header_done:
                        header_done = True
                html.append('</table>')
                table_rows = []

        # Bold
        line = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', line)
        # Inline code
        line = re.sub(r'`(.+?)`', r'<code style="background:#fef3c7;padding:1px 4px;border-radius:3px;font-size:0.9em;">\1</code>', line)

        # Empty line
        if not line.strip():
            html.append('<br>')
        else:
            html.append(f'<p style="margin:4px 0;line-height:1.6;">{line}</p>')

    # Close any remaining table
    if in_table and table_rows:
        html.append('<table style="width:100%;border-collapse:collapse;margin:10px 0;font-size:0.85em;">')
        header_done = False
        for row in table_rows:
            if row == '__SEP__':
                header_done = True
                continue
            tag = 'th' if not header_done else 'td'
            style_td = 'border:1px solid #d1d5db;padding:6px 10px;text-align:left;'
            style_th = 'border:1px solid #d1d5db;padding:6px 10px;text-align:left;background:#f8fafc;font-weight:600;'
            cells_html = ''.join(f'<{tag} style="{style_th if tag=="th" else style_td}">{c}</{tag}>' for c in row)
            html.append(f'<tr>{cells_html}</tr>')
            if not header_done:
                header_done = True
        html.append('</table>')

    return '\n'.join(html)


class MappingHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=BASE_DIR, **kwargs)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        # API: Full data (gzipped)
        if path == '/api/data':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Encoding', 'gzip')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            with open(DATA_FILE, 'rb') as f:
                self.wfile.write(f.read())
            return

        # API: Cross-refs only (lighter)
        if path == '/api/refs':
            self.send_json(MAPPING_DATA['cross_refs'])
            return

        # API: Search
        if path == '/api/search':
            qs = urllib.parse.parse_qs(parsed.query)
            query = qs.get('q', [''])[0].strip()
            table = qs.get('table', ['all'])[0]
            results = self.search(query, table)
            self.send_json(results)
            return

        # API: Get instructions data
        if path == '/api/instructions':
            self.send_json(get_instructions())
            return

        # API: Get knowledge note
        if path == '/api/note':
            qs = urllib.parse.parse_qs(parsed.query)
            keyword = qs.get('k', [''])[0].strip()
            result = self.get_note(keyword)
            self.send_json(result)
            return

        # API: Get linked items
        if path == '/api/linked':
            qs = urllib.parse.parse_qs(parsed.query)
            item_id = qs.get('id', [''])[0]
            table = qs.get('table', [''])[0]
            results = self.get_linked(item_id, table)
            self.send_json(results)
            return

        # Default: serve static files
        super().do_GET()

    def send_json(self, data):
        payload = json.dumps(data, ensure_ascii=False).encode('utf-8')
        compressed = gzip.compress(payload, compresslevel=6)

        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Encoding', 'gzip')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(compressed)

    def search(self, query, table='all'):
        """Search across tables (SH -> TS -> ICD9)"""
        if not query:
            return {'results': [], 'total': 0}

        qlow = query.lower()
        results = []

        tables_to_search = [table] if table != 'all' else ['shanghai', 'tech_specs', 'icd9']

        for t in tables_to_search:
            items = MAPPING_DATA.get(t, [])
            for item in items:
                # Search in name, code, desc
                search_text = ' '.join([
                    str(item.get(k, '')) for k in item.keys()
                ]).lower()
                if qlow in search_text:
                    results.append({
                        'table': t,
                        'id': item['id'],
                        'item': item,
                    })
                    if len(results) >= 50:
                        break
            if len(results) >= 50:
                break

        return {'results': results[:50], 'total': len(results)}

    def get_linked(self, item_id, table):
        """Get all cross-refs for a given item (SH -> TS -> ICD9 only).

        Returns:
          refs: all cross-ref records
          linked: grouped items with relationship metadata
          direct_ids: IDs of directly linked items per table
        """
        if not item_id or not table:
            return {'refs': [], 'linked': {}, 'direct_ids': {}}

        index_key = {'shanghai': 'sh', 'tech_specs': 'ts', 'icd9': 'icd9'}
        idx = index_key.get(table, '')
        if not idx:
            return {'refs': [], 'linked': {}, 'direct_ids': {}}

        ref_indices = MAPPING_DATA['_index'].get(idx, {}).get(item_id, [])
        direct_refs = [MAPPING_DATA['cross_refs'][i] for i in ref_indices]

        refs = direct_refs

        # Read ICD-10 lookup map
        icd10_map = MAPPING_DATA.get('_icd10_map', {})

        # Collect linked items with relationship metadata
        linked = {'shanghai': [], 'tech_specs': [], 'icd9': []}
        direct_ids = {'shanghai': set(), 'tech_specs': set(), 'icd9': set()}

        def resolve_item(table_key, ref_id):
            """Find item in the appropriate data array by ID."""
            if table_key == 'shanghai':
                for s in MAPPING_DATA['shanghai']:
                    if s['id'] == ref_id:
                        return s.copy() if isinstance(s, dict) else s
            elif table_key == 'tech_specs':
                for t in MAPPING_DATA['tech_specs']:
                    if t['id'] == ref_id:
                        return t.copy() if isinstance(t, dict) else t
            elif table_key == 'icd9':
                for i in MAPPING_DATA['icd9']:
                    if i['id'] == ref_id:
                        return i.copy() if isinstance(i, dict) else i
            return None

        for ref in direct_refs:
            # Linked SH items
            if ref['sh_id'] and ref['sh_id'] != item_id:
                item = resolve_item('shanghai', ref['sh_id'])
                if item:
                    linked['shanghai'].append(item)
                    direct_ids['shanghai'].add(ref['sh_id'])

            # Linked TS items
            if ref['ts_id']:
                item = resolve_item('tech_specs', ref['ts_id'])
                if item:
                    linked['tech_specs'].append(item)
                    direct_ids['tech_specs'].add(ref['ts_id'])

            # Linked ICD-9 items
            if ref['icd9_id']:
                item = resolve_item('icd9', ref['icd9_id'])
                if item:
                    linked['icd9'].append(item)
                    direct_ids['icd9'].add(ref['icd9_id'])

        # Deduplicate and attach relationship metadata
        for k in linked:
            seen = set()
            unique = []
            for item in linked[k]:
                iid = item['id']
                if iid not in seen:
                    seen.add(iid)
                    item['_rel'] = 'direct'
                    # Attach ICD-10 if available
                    if k in ('shanghai', 'tech_specs'):
                        item_name = item.get('name', '')
                        if item_name in icd10_map:
                            item['_icd10'] = icd10_map[item_name]
                    unique.append(item)
            linked[k] = unique

        return {
            'refs': refs,
            'linked': linked,
            'direct_ids': {k: list(v) for k, v in direct_ids.items()},
            'stats': {
                'shanghai': len(linked['shanghai']),
                'tech_specs': len(linked['tech_specs']),
                'icd9': len(linked['icd9']),
            }
        }

    def get_note(self, keyword):
        """Look up and return knowledge note content for a keyword"""
        if not keyword:
            return {'found': False, 'html': ''}

        # Check keyword against registry
        note_file = None
        for k, filename in NOTE_REGISTRY.items():
            if k in keyword:
                note_file = filename
                break

        if not note_file:
            return {'found': False, 'html': '', 'keyword': keyword}

        md_content = load_note(note_file)
        if not md_content:
            return {'found': False, 'html': '', 'keyword': keyword}

        html = md_to_html(md_content)
        return {'found': True, 'html': html, 'keyword': keyword, 'source': note_file}

    def log_message(self, format, *args):
        # Quiet logging
        pass


if __name__ == '__main__':
    PORT = 8768
    server = http.server.HTTPServer(('0.0.0.0', PORT), MappingHandler)
    print(f"4-way Mapping Server running at http://localhost:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
