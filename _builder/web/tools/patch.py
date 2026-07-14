#!/usr/bin/env python3
"""
Safe JS patcher for app.js — applies text replacements with backup.
Usage: python3 tools/patch.py "old_string" "new_string" [--dry-run]
"""
import sys, os, shutil
from datetime import datetime

DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JS = os.path.join(DIR, 'app.js')

def patch(old, new, dry_run=False):
    with open(JS, 'r', encoding='utf-8') as f:
        content = f.read()

    count = content.count(old)
    if count == 0:
        print(f"ERROR: old_string not found in app.js")
        return False
    if count > 1:
        print(f"WARN: old_string found {count} times — will replace ALL occurrences")

    new_content = content.replace(old, new)

    if dry_run:
        print(f"DRY RUN: would replace {count} occurrence(s)")
        # Show first diff
        lines_old = content.split('\n')
        lines_new = new_content.split('\n')
        for i, (lo, ln) in enumerate(zip(lines_old, lines_new)):
            if lo != ln:
                print(f"  Line {i+1}:")
                print(f"  - {lo.strip()[:120]}")
                print(f"  + {ln.strip()[:120]}")
                break
        return True

    # Backup
    backup = JS + f'.bak.{datetime.now().strftime("%Y%m%d_%H%M%S")}'
    shutil.copy2(JS, backup)
    print(f"Backup: {backup}")

    with open(JS, 'w', encoding='utf-8') as f:
        f.write(new_content)

    print(f"OK: replaced {count} occurrence(s)")
    return True

if __name__ == "__main__":
    dry = '--dry-run' in sys.argv
    args = [a for a in sys.argv[1:] if a != '--dry-run']
    if len(args) < 2:
        print("Usage: python3 tools/patch.py 'old' 'new' [--dry-run]")
        sys.exit(1)
    ok = patch(args[0], args[1], dry_run=dry)
    sys.exit(0 if ok else 1)
