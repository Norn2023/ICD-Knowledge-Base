"""Drug Directory HTTP Server - serves JSON, PDFs, and page text extraction"""
from http.server import HTTPServer, SimpleHTTPRequestHandler
import os, json, urllib.parse, re, time

DIR = os.path.dirname(os.path.abspath(__file__))

# ── Drug instruction manual field extraction ──
_RE_DRUG_FIELDS = [
    ('reg_name',    r'通用名称[：:]\s*([^\n]+)'),
    ('trade_name',  r'商品名称[：:]\s*([^\n]+)'),
    ('en_name',     r'英文名称[：:]\s*([^\n]+)'),
    ('pinyin',      r'汉语拼音[：:]\s*([^\n]+)'),
    ('spec',        r'【规格】\s*\n?\s*([^\n【]+)'),
    ('packaging',   r'【包装】\s*\n?\s*([^【]+?)(?:\n【|$)'),
    ('approval',    r'(?:【批准文号】|批准文号)[：:\s]*((?:国药)?[准字包字][\w]+)'),
    ('manufacturer', r'(?:【生产企业】|【药品上市许可持有人】)[\s\S]*?名称[：:]\s*([^\n]+)'),
    ('exec_std',    r'【执行标准】\s*\n?\s*([^\n【]+)'),
    ('validity',    r'【有效期】\s*\n?\s*([^\n【]+)'),
    ('dosage_form', r'注册剂型[：:]\s*([^\n]+)'),
]

def _extract_drug_fields(filepath, filedata=None):
    """Extract key fields from uploaded drug instruction PDF. Returns dict."""
    result = {}
    ext = os.path.splitext(filepath)[1].lower()
    if ext != '.pdf':
        return result

    try:
        import fitz
        # Use filedata if provided (saves re-reading), else open file
        if filedata:
            doc = fitz.open(stream=filedata, filetype='pdf')
        else:
            doc = fitz.open(filepath)

        all_text = []
        for i in range(doc.page_count):
            t = doc[i].get_text('text')
            all_text.append(t)
        doc.close()

        full_text = '\n'.join(all_text)

        # Detect encoding: check for garbled latin-1 UTF-8 pattern
        if '【药品名称】' not in full_text and '通用名称' not in full_text:
            # Try latin-1 → utf-8 recovery
            recovered = []
            for t in all_text:
                try:
                    recovered.append(t.encode('latin-1').decode('utf-8', errors='replace'))
                except:
                    recovered.append(t)
            full_text = '\n'.join(recovered)

        # If still no recognizable drug info markers, PDF may be scanned
        if '通用名称' not in full_text and '【药品名称】' not in full_text:
            return result

        # Extract fields using regex patterns
        for field_name, pattern in _RE_DRUG_FIELDS:
            m = re.search(pattern, full_text)
            if m:
                val = m.group(1).strip()
                # Clean up: remove leading/trailing whitespace, collapse newlines
                val = re.sub(r'\s+', ' ', val).strip()
                if val and len(val) > 1:
                    result[field_name] = val

        # Infer dosage_form from drug name if not found
        if 'dosage_form' not in result and 'reg_name' in result:
            name = result['reg_name']
            forms = ['注射用', '注射液', '片', '胶囊', '颗粒', '口服液', '糖浆', '丸',
                     '软膏', '乳膏', '凝胶', '滴眼液', '滴耳液', '喷雾剂', '气雾剂',
                     '栓', '贴膏', '贴剂', '洗剂', '搽剂', '散', '吸入剂']
            for fm in forms:
                if fm in name:
                    result['dosage_form'] = fm
                    break

        # Try to get manufacturer from 企业名称 if not found via 【生产企业】
        if 'manufacturer' not in result:
            m = re.search(r'企业名称[：:]\s*([^\n]+)', full_text)
            if m:
                result['manufacturer'] = m.group(1).strip()

        # Try broader approval number pattern
        if 'approval' not in result:
            m = re.search(r'(?:批准文号|国药准字)[：:\s]*([\w]+)', full_text)
            if m:
                val = m.group(1).strip()
                if len(val) >= 8:
                    result['approval'] = '国药准字' + val if not val.startswith('国药') else val

        return result
    except Exception as e:
        print(f'[extract] Error: {e}')
        return {}

# ── Shared text reformatter (also in pre_extract_text.py) ──
_RE_PAGE_NUM_SRV = re.compile(r'^\s*\d{1,4}\s*$')
_RE_HEADER_SRV = re.compile(r'^(中国药典\d{4}年版|中华人民共和国药典.*|临床用药须知.*)$')
_RE_SECTION_SRV = re.compile(r'^[【〔［\[]')
_RE_CHAPTER_SRV = re.compile(r'^第[一二三四五六七八九十百千\d]+[章节篇]')

def reformat_text(raw_text):
    lines = [l.strip() for l in raw_text.split('\n') if l.strip()]
    if not lines: return raw_text
    cleaned = []
    for line in lines:
        if _RE_PAGE_NUM_SRV.match(line) and len(line) <= 4: continue
        if _RE_HEADER_SRV.match(line): continue
        if line in ('2025年版', '2020年版'): continue
        cleaned.append(line)
    if not cleaned: return raw_text
    merged = []; buf = ''
    for line in cleaned:
        if _RE_SECTION_SRV.match(line) or _RE_CHAPTER_SRV.match(line):
            if buf: merged.append(buf); buf = ''
            merged.append(line); continue
        cjk = sum(1 for c in line if '一' <= c <= '鿿')
        if len(line) <= 8 and cjk <= 4:
            if buf: merged.append(buf); buf = ''
            merged.append(line); continue
        ascii_n = sum(1 for c in line if ord(c) < 128)
        if ascii_n > len(line) * 0.6:
            if buf: merged.append(buf); buf = ''
            merged.append(line); continue
        if not buf:
            buf = line
        elif buf[-1] not in '。！？…）】」』》)' and buf[-1] not in '，、；：':
            buf += line
        else:
            merged.append(buf); buf = line
    if buf: merged.append(buf)
    return '\n'.join(merged)

# Load page text cache (pre-extracted from PDFs) at startup
PAGE_CACHE = {}
_cache_path = os.path.join(DIR, 'page_cache.json')
if os.path.exists(_cache_path):
    import json as _json_module
    with open(_cache_path, 'r', encoding='utf-8') as _f:
        PAGE_CACHE = _json_module.load(_f)
    print(f'[cache] Loaded {len(PAGE_CACHE)} pages')
else:
    print('[cache] page_cache.json not found, preview will open PDF directly')

class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIR, **kwargs)

    def end_headers(self):
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
        self.send_header('Access-Control-Allow-Origin', '*')
        super().end_headers()

    def _parse_multipart(self, body, boundary):
        """Simple multipart form-data parser. Returns dict of field_name -> (filename, data)."""
        delimiter = ('--' + boundary).encode()
        parts = body.split(delimiter)
        result = {}
        for part in parts:
            if not part or part == b'--\r\n' or part == b'--':
                continue
            if b'\r\n\r\n' in part:
                headers_section, data = part.split(b'\r\n\r\n', 1)
                headers_text = headers_section.decode('utf-8', errors='ignore')
                name_match = re.search(r'name="([^"]*)"', headers_text)
                if not name_match:
                    continue
                field_name = name_match.group(1)
                fn_match = re.search(r'filename="([^"]*)"', headers_text)
                filename = fn_match.group(1) if fn_match else None
                data = data.rstrip(b'\r\n')
                if data.endswith(b'--'):
                    data = data[:-2].rstrip(b'\r\n')
                result[field_name] = (filename, data)
        return result

    def do_POST(self):
        if self.path.startswith('/upload'):
            try:
                qs = urllib.parse.urlparse(self.path).query
                params = urllib.parse.parse_qs(qs)
                drug_name = params.get('drug', ['unknown'])[0]
                content_type = self.headers.get('Content-Type', '')
                if 'boundary=' not in content_type:
                    self.send_error(400, 'Missing boundary')
                    return
                boundary = content_type.split('boundary=')[1].strip()
                content_length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(content_length)
                fields = self._parse_multipart(body, boundary)
                if 'file' not in fields:
                    self.send_error(400, 'No file field')
                    return
                filename, filedata = fields['file']
                if not filename or not filedata:
                    self.send_error(400, 'Empty file')
                    return
                filename = os.path.basename(filename)
                safe_drug = re.sub(r'[^\w一-鿿\-]', '_', drug_name)
                upload_dir = os.path.join(DIR, 'uploads', safe_drug)
                os.makedirs(upload_dir, exist_ok=True)
                ts = int(time.time())
                save_name = f'{ts}_{filename}'
                filepath = os.path.join(upload_dir, save_name)
                with open(filepath, 'wb') as f:
                    f.write(filedata)

                # Extract drug fields from PDF
                extracted = _extract_drug_fields(filepath, filedata)
                # Save extracted fields as sidecar metadata
                meta_name = os.path.splitext(save_name)[0] + '.meta.json'
                meta_path = os.path.join(upload_dir, meta_name)
                with open(meta_path, 'w', encoding='utf-8') as mf:
                    json.dump(extracted, mf, ensure_ascii=False)

                result = json.dumps({
                    'ok': True, 'filename': filename,
                    'saved_as': save_name,
                    'url': f'/uploads/{urllib.parse.quote(safe_drug)}/{urllib.parse.quote(save_name)}',
                    'extracted': extracted
                }, ensure_ascii=False)
                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                data = result.encode('utf-8')
                self.send_header('Content-Length', str(len(data)))
                self.end_headers()
                self.wfile.write(data)
                return
            except Exception as e:
                self.send_error(500, str(e))
                return
        self.send_error(405, 'Method not allowed')

    def do_GET(self):
        # File ID mapping (for URL-safe access)
        file_map = {}
        for f in os.listdir(DIR):
            if f.endswith('.pdf'):
                # Create URL-safe ID from filename
                fid = f.encode('utf-8').hex()[:16]
                # Also map by simple keys
                if '药典1部' in f: file_map['pharm1'] = f
                elif '药典2部' in f: file_map['pharm2'] = f
                elif '化学药' in f: file_map['chem'] = f
                elif '处方集' in f: file_map['rx'] = f

        # Page text extraction API: /page_text?id=chem&page=123 or /page_text?file=xxx&page=123
        if self.path.startswith('/page_text?'):
            try:
                qs = urllib.parse.urlparse(self.path).query
                params = urllib.parse.parse_qs(qs)
                fid = params.get('id', [''])[0]
                fname = params.get('file', [''])[0]
                page = int(params.get('page', ['1'])[0])

                # Resolve file ID
                if fid and fid in file_map:
                    fname = file_map[fid]
                elif not fname:
                    self.send_error(400, 'Missing id or file parameter')
                    return

                fname = os.path.basename(fname)
                fpath = os.path.join(DIR, fname)
                if not os.path.exists(fpath):
                    self.send_error(404, 'File not found: ' + fname)
                    return

                # Check page cache first (instant lookup)
                cache_key = f'{fid}|{page}'
                if cache_key in PAGE_CACHE:
                    result = json.dumps({
                        'page': page, 'total_pages': 0,
                        'text': PAGE_CACHE[cache_key][:8000]
                    }, ensure_ascii=False)
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json; charset=utf-8')
                    data = result.encode('utf-8')
                    self.send_header('Content-Length', str(len(data)))
                    self.end_headers()
                    self.wfile.write(data)
                    return

                import fitz
                doc = fitz.open(fpath)
                if page < 1 or page > doc.page_count:
                    doc.close()
                    self.send_error(400, f'Page out of range (1-{doc.page_count})')
                    return

                text = reformat_text(doc[page - 1].get_text())
                total = doc.page_count
                doc.close()

                result = json.dumps({
                    'page': page, 'total_pages': total,
                    'text': text[:8000]
                }, ensure_ascii=False)

                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                data = result.encode('utf-8')
                self.send_header('Content-Length', str(len(data)))
                self.end_headers()
                self.wfile.write(data)
                return
            except Exception as e:
                self.send_error(500, str(e))
                return

        # Gzip JSON serving
        if self.path.endswith('.json'):
            gz = os.path.join(DIR, self.path.lstrip('/') + '.gz')
            if os.path.exists(gz):
                with open(gz, 'rb') as f:
                    data = f.read()
                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.send_header('Content-Encoding', 'gzip')
                self.send_header('Content-Length', str(len(data)))
                self.end_headers()
                self.wfile.write(data)
                return

        # PDF serving by file ID: /pdf?id=chem or /pdf?id=pharm1
        if self.path.startswith('/pdf?'):
            qs = urllib.parse.urlparse(self.path).query
            params = urllib.parse.parse_qs(qs)
            fid = params.get('id', [''])[0]
            if fid in file_map:
                fname = file_map[fid]
                fpath = os.path.join(DIR, fname)
                size = os.path.getsize(fpath)
                self.send_response(200)
                self.send_header('Content-Type', 'application/pdf')
                self.send_header('Content-Length', str(size))
                self.send_header('Accept-Ranges', 'bytes')
                self.end_headers()
                with open(fpath, 'rb') as f:
                    while True:
                        chunk = f.read(65536)
                        if not chunk: break
                        self.wfile.write(chunk)
                return

        # Uploads file listing API: /uploads_list?drug=xxx
        if self.path.startswith('/uploads_list?'):
            qs = urllib.parse.urlparse(self.path).query
            params = urllib.parse.parse_qs(qs)
            drug_name = params.get('drug', [''])[0]
            safe_drug = re.sub(r'[^\w一-鿿\-]', '_', drug_name)
            upload_dir = os.path.join(DIR, 'uploads', safe_drug)
            files = []
            if os.path.isdir(upload_dir):
                for f in sorted(os.listdir(upload_dir), reverse=True):
                    if f.endswith('.meta.json'):
                        continue  # Skip metadata files in listing
                    fpath = os.path.join(upload_dir, f)
                    if os.path.isfile(fpath):
                        entry = {
                            'name': f,
                            'size': os.path.getsize(fpath),
                            'url': f'/uploads/{urllib.parse.quote(safe_drug)}/{urllib.parse.quote(f)}'
                        }
                        # Load sidecar metadata if exists
                        meta_name = os.path.splitext(f)[0] + '.meta.json'
                        meta_path = os.path.join(upload_dir, meta_name)
                        if os.path.isfile(meta_path):
                            try:
                                with open(meta_path, 'r', encoding='utf-8') as mf:
                                    entry['extracted'] = json.load(mf)
                            except:
                                pass
                        files.append(entry)
            result = json.dumps({'files': files}, ensure_ascii=False)
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            data = result.encode('utf-8')
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return

        # Serve uploaded files
        if self.path.startswith('/uploads/'):
            rel_path = urllib.parse.unquote(self.path.lstrip('/'))
            fpath = os.path.join(DIR, rel_path)
            if os.path.isfile(fpath):
                ext = os.path.splitext(fpath)[1].lower()
                ct_map = {'.pdf':'application/pdf','.jpg':'image/jpeg','.jpeg':'image/jpeg',
                          '.png':'image/png','.gif':'image/gif','.doc':'application/msword',
                          '.docx':'application/vnd.openxmlformats-officedocument.wordprocessingml.document'}
                ct = ct_map.get(ext, 'application/octet-stream')
                size = os.path.getsize(fpath)
                self.send_response(200)
                self.send_header('Content-Type', ct)
                self.send_header('Content-Length', str(size))
                self.end_headers()
                with open(fpath, 'rb') as f:
                    while True:
                        chunk = f.read(65536)
                        if not chunk: break
                        self.wfile.write(chunk)
                return

        super().do_GET()

port = 8766
print(f'药品目录 http://localhost:{port}')
HTTPServer(('', port), Handler).serve_forever()
