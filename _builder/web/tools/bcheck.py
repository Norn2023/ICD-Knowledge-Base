#!/usr/bin/env python3
"""
Quick brace balance checker for app.js. No dependencies.
"""
import re, os

JS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'app.js')

with open(JS, 'r', encoding='utf-8') as f:
    code = f.read()

# Strip strings, comments, regex
clean = code
clean = re.sub(r'"(?:[^"\\]|\\.)*"', '""', clean)
clean = re.sub(r"'(?:[^'\\]|\\.)*'", "''", clean)
clean = re.sub(r'`(?:[^`\\]|\\.)*`', '``', clean)
clean = re.sub(r'//[^\n]*', '', clean)
clean = re.sub(r'/\*.*?\*/', '', clean, re.DOTALL)

balance = {'{': 0, '(': 0, '[': 0}
pairs = {'}': '{', ')': '(', ']': '['}

for i, ch in enumerate(clean):
    if ch in balance:
        balance[ch] += 1
    elif ch in pairs:
        balance[pairs[ch]] -= 1
        if balance[pairs[ch]] < 0:
            line = code[:code.find(clean[:i+1])].count('\n') + 1  # approx
            print(f"FAIL: Extra {ch} around line {line}")
            exit(1)

errs = [f"{b}: {'+' if v>0 else ''}{v}" for b, v in balance.items() if v != 0]
if errs:
    print(f"FAIL: {', '.join(errs)}")
else:
    print("OK: braces balanced")
