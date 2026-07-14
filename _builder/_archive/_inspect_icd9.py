import sys
import re
sys.stdout.reconfigure(encoding='utf-8')

with open('ICD-9-CM3医保2(2026年5月从医保局官网下载）.xlsx', 'r', encoding='utf-8') as f:
    html = f.read()

print(f'File size: {len(html):,} chars')
tables = re.findall(r'<table[^>]*>', html, re.I)
print(f'<table> tags: {len(tables)}')
print(f'</table> tags: {len(re.findall(r"</table>", html, re.I))}')

rows = re.findall(r'<tr[^>]*>', html, re.I)
print(f'<tr> tags: {len(rows)}')

tds = re.findall(r'<td[^>]*>', html, re.I)
print(f'<td> tags: {len(tds)}')

row_contents = re.findall(r'<tr[^>]*>(.*?)</tr>', html, re.DOTALL | re.I)
print(f'\nExtracted {len(row_contents)} rows')

print('\n--- First 5 rows ---')
for i, r in enumerate(row_contents[:5]):
    cells = re.findall(r'<td[^>]*>(.*?)</td>', r, re.DOTALL | re.I)
    cleaned = [re.sub(r'<[^>]+>', '', c).strip()[:50] for c in cells]
    print(f'Row {i}: {len(cells)} cells: {cleaned}')

print('\n--- Last 5 rows ---')
for i, r in enumerate(row_contents[-5:]):
    cells = re.findall(r'<td[^>]*>(.*?)</td>', r, re.DOTALL | re.I)
    cleaned = [re.sub(r'<[^>]+>', '', c).strip()[:50] for c in cells]
    print(f'Row {len(row_contents)-5+i}: {len(cells)} cells: {cleaned}')

# Check for merged cells or rowspan
print('\n--- Merged cells ---')
merged = re.findall(r'rowspan|colspan|merge', html, re.I)
print(f'Merge attributes found: {len(merged)}')
