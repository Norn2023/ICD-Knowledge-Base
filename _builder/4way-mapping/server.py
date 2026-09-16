"""
医疗服务价格映射系统 - Port 8768
支持多省份数据展示和四方映射
"""
import http.server
import json
import gzip
import os
import re
import urllib.parse

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, 'data.json.gz')

# 省份数据映射
PROVINCE_DATA = {
    'shanghai': '上海市',
    'beijing': '北京市',
    'guangdong': '广东省',
    'jiangsu': '江苏省',
    'zhejiang': '浙江省'
}

# Load data on startup
MAPPING_DATA = {}
try:
    with gzip.open(DATA_FILE, 'rb') as f:
        MAPPING_DATA = json.loads(f.read().decode('utf-8'))
    print(f"Loaded data: {len(MAPPING_DATA.get('shanghai',[]))} Shanghai items")
except Exception as e:
    print(f"Warning: Data load failed: {e}")
    MAPPING_DATA = {
        'shanghai': [],
        'pricing_guide': [],
        'tech_specs': [],
        'icd9': [],
        'cross_refs': []
    }

class MappingHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=BASE_DIR, **kwargs)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        # API: Get provinces list
        if path == '/api/provinces':
            self.send_json({'provinces': PROVINCE_DATA})
            return

        # API: Get items by province
        if path == '/api/items':
            qs = urllib.parse.parse_qs(parsed.query)
            province = qs.get('province', ['shanghai'])[0]
            table = qs.get('table', ['all'])[0]
            limit = int(qs.get('limit', [100])[0])
            offset = int(qs.get('offset', [0])[0])

            # Get items based on province
            items = MAPPING_DATA.get(province, [])
            total = len(items)
            page_items = items[offset:offset+limit]

            self.send_json({
                'items': page_items,
                'total': total,
                'limit': limit,
                'offset': offset,
                'province': province,
                'province_name': PROVINCE_DATA.get(province, province)
            })
            return

        # API: Search
        if path == '/api/search':
            qs = urllib.parse.parse_qs(parsed.query)
            query = qs.get('q', [''])[0].strip()
            province = qs.get('province', ['shanghai'])[0]
            limit = int(qs.get('limit', [50])[0])

            items = MAPPING_DATA.get(province, [])
            results = []
            qlow = query.lower()

            for item in items:
                search_text = ' '.join([str(item.get(k, '')) for k in item.keys() if k != 'id']).lower()
                if qlow in search_text:
                    results.append(item)
                    if len(results) >= limit:
                        break

            self.send_json({'results': results, 'total': len(results), 'province': province})
            return

        # API: Get mapping for an item
        if path == '/api/mapping':
            qs = urllib.parse.parse_qs(parsed.query)
            item_id = qs.get('id', [''])[0]
            province = qs.get('province', ['shanghai'])[0]

            result = self.get_mapping(item_id, province)
            self.send_json(result)
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

    def get_mapping(self, item_id, province):
        """Get mapping for an item across all 4 tables"""
        if not item_id:
            return {'error': 'No item_id provided'}

        # Find source item
        source_table = None
        source_item = None

        # Check province data
        for table in ['shanghai', 'pricing_guide', 'tech_specs', 'icd9']:
            for item in MAPPING_DATA.get(table, []):
                if item.get('id') == item_id:
                    source_table = table
                    source_item = item
                    break
            if source_table:
                break

        # Also check province-specific data
        province_data = MAPPING_DATA.get(province, [])
        for item in province_data:
            if item.get('id') == item_id:
                source_table = province
                source_item = item
                break

        if not source_table:
            return {'error': 'Item not found', 'item_id': item_id}

        # Build mapping result
        result = {
            'source_table': source_table,
            'source_item': source_item,
            'province': province,
            'province_name': PROVINCE_DATA.get(province, province),
            'mappings': [],
            'stats': {}
        }

        return result

    def log_message(self, format, *args):
        pass

if __name__ == '__main__':
    PORT = 8768
    while True:
        try:
            server = http.server.HTTPServer(('0.0.0.0', PORT), MappingHandler)
            print(f"Medical Service Price System at http://localhost:{PORT}")
            print(f"Provinces: {list(PROVINCE_DATA.keys())}")
            server.serve_forever()
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError, OSError):
            continue
        except KeyboardInterrupt:
            break
