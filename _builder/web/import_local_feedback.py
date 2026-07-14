#!/usr/bin/env python3
"""
将贵院历史医保病例 CSV 转换为 local_feedback.json
用法: python import_local_feedback.py your_export.csv
"""
import csv
import json
import sys
from collections import defaultdict

def main():
    if len(sys.argv) < 2:
        print("用法: python import_local_feedback.py <csv文件>")
        print("\nCSV 需要以下列:")
        print("  主要诊断编码, 医保反馈病组编码, 医保反馈是否MCC, 医保反馈是否CC")
        print("\n也支持英文列名:")
        print("  main_dx_code, group_code, is_mcc, is_cc")
        sys.exit(1)

    csv_file = sys.argv[1]

    # 列名映射（支持中文和英文）
    col_map = {
        '主要诊断编码': 'main_dx',
        'main_dx_code': 'main_dx',
        '医保反馈病组编码': 'group_code',
        'group_code': 'group_code',
        '医保反馈是否MCC': 'is_mcc',
        'is_mcc': 'is_mcc',
        '医保反馈是否CC': 'is_cc',
        'is_cc': 'is_cc',
    }

    cases = []
    group_stats = defaultdict(lambda: {'total': 0, 'mcc_count': 0, 'cc_count': 0, 'no_cc_count': 0})

    with open(csv_file, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        # Normalize headers
        normalized = {}
        for header in reader.fieldnames:
            header = header.strip()
            if header in col_map:
                normalized[col_map[header]] = header

        for row in reader:
            main_dx = row.get(normalized.get('main_dx', ''), '').strip().upper()
            group_code = row.get(normalized.get('group_code', ''), '').strip()
            is_mcc = row.get(normalized.get('is_mcc', ''), '').strip()
            is_cc = row.get(normalized.get('is_cc', ''), '').strip()

            if not main_dx or not group_code:
                continue

            # 提取诊断前缀（4位，如 D25.）
            dx_prefix = main_dx[:4] if len(main_dx) >= 4 else main_dx

            # 判定 MCC/CC/noCC
            if is_mcc in ('1', '是', 'YES', 'yes', 'Y', 'y'):
                mcc_level = 'MCC'
            elif is_cc in ('1', '是', 'YES', 'yes', 'Y', 'y'):
                mcc_level = 'CC'
            else:
                mcc_level = 'noCC'

            cases.append({
                'main_dx_prefix': dx_prefix,
                'group_code': group_code,
                'hist_mcc_level': mcc_level,
            })

            group_stats[group_code]['total'] += 1
            if mcc_level == 'MCC':
                group_stats[group_code]['mcc_count'] += 1
            elif mcc_level == 'CC':
                group_stats[group_code]['cc_count'] += 1
            else:
                group_stats[group_code]['no_cc_count'] += 1

    # 去重（同诊断前缀+同分组只保留一条）
    seen = set()
    unique_cases = []
    for c in cases:
        key = (c['main_dx_prefix'], c['group_code'])
        if key not in seen:
            seen.add(key)
            unique_cases.append(c)

    # 输出
    output = {
        'version': '1.0',
        'description': '本地医院历史医保反馈数据',
        'source': csv_file,
        'total_records': len(cases),
        'unique_cases': len(unique_cases),
        'cases': unique_cases,
        'groups': {k: dict(v) for k, v in group_stats.items()}
    }

    output_file = '_builder/web/local_feedback.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"✅ 转换完成!")
    print(f"   总记录: {len(cases)}")
    print(f"   去重后: {len(unique_cases)}")
    print(f"   涉及分组: {len(group_stats)}")
    print(f"   输出: {output_file}")

    # 显示前缀统计
    prefix_counts = defaultdict(int)
    for c in unique_cases:
        prefix_counts[c['main_dx_prefix']] += 1
    print(f"\n诊断前缀统计（前10）:")
    for prefix, count in sorted(prefix_counts.items(), key=lambda x: -x[1])[:10]:
        print(f"  {prefix}: {count} 例")

if __name__ == '__main__':
    main()
