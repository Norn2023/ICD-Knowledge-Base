#!/usr/bin/env python3
"""Persistent web app validator - validates JS syntax, file references, brace balance"""
import re, os, sys

DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def check_brace_balance(js_path):
    """Count { } ( ) [ ] balance in JS file, ignoring strings and comments"""
    with open(js_path, 'r', encoding='utf-8') as f:
        code = f.read()

    # Strip strings and comments
    clean = re.sub(r'"(?:[^"\\]|\\.)*"', '""', code)
    clean = re.sub(r"'(?:[^'\\]|\\.)*'", "''", clean)
    clean = re.sub(r'`(?:[^`\\]|\\.)*`', '``', clean)
    clean = re.sub(r'//.*$', '', clean, flags=re.MULTILINE)
    clean = re.sub(r'/\*.*?\*/', '', clean, flags=re.DOTALL)

    counts = {'{': 0, '(': 0, '[': 0}
    for ch in clean:
        if ch in counts: counts[ch] += 1
        elif ch == '}': counts['{'] -= 1
        elif ch == ')': counts['('] -= 1
        elif ch == ']': counts['['] -= 1

    errors = []
    for brace, balance in counts.items():
        if balance != 0:
            errors.append(f"{brace}: {'+' if balance > 0 else ''}{balance}")
    return errors

def check_html_refs(html_path):
    """Check that <link>, <script src> references point to existing files"""
    with open(html_path, 'r', encoding='utf-8') as f:
        html = f.read()

    refs = re.findall(r'(?:href|src)="([^"]+\.(?:css|js))"', html)
    missing = []
    for ref in refs:
        path = os.path.join(DIR, ref)
        if not os.path.exists(path):
            missing.append(ref)
    return missing

if __name__ == "__main__":
    ok = True

    # 1. Check app.js brace balance
    js = os.path.join(DIR, 'app.js')
    if os.path.exists(js):
        be = check_brace_balance(js)
        if be:
            print(f"FAIL: app.js brace balance: {', '.join(be)}")
            ok = False
        else:
            print("OK: app.js brace balance")
    else:
        print("SKIP: app.js not found (inline script in index.html?)")

    # 2. Check HTML references
    html = os.path.join(DIR, 'index.html')
    missing = check_html_refs(html)
    if missing:
        print(f"FAIL: Missing references: {', '.join(missing)}")
        ok = False
    else:
        print("OK: index.html references")

    # 3. Check JSON files exist
    for f in ['data.json', 'detail.json', 'drg.json']:
        path = os.path.join(DIR, f)
        gz = path + '.gz'
        if os.path.exists(path):
            sz = os.path.getsize(path)
            print(f"OK: {f} ({sz/1024/1024:.1f} MB)")
        elif os.path.exists(gz):
            sz = os.path.getsize(gz)
            print(f"OK: {f}.gz ({sz/1024:.1f} MB)")
        else:
            print(f"WARN: {f} missing")

    sys.exit(0 if ok else 1)
