---
title: "ICD知识库Web应用 - 项目架构"
created: 2026-06-19
tags:
  - icd
  - web-app
  - architecture
  - reference
---

## 项目位置
`_builder/` — 数据构建管道
`_builder/web/` — Web 应用（HTTP服务于此目录）

## 文件结构

### Web 前端
| 文件 | 大小 | 用途 |
|------|------|------|
| `index.html` | 6.4 KB | HTML 结构 + 导航 |
| `style.css` | 6.8 KB | 所有 CSS 样式 |
| `app.js` | 33 KB | 所有 JavaScript 逻辑 |

### 数据文件 (gzip 传输)
| 文件 | 原始大小 | Gzip大小 | 内容 |
|------|---------|----------|------|
| `data.json` | 10.8 MB | 1.2 MB | ICD-10/ICD-9 编码 + 临床映射 + DIP |
| `detail.json` | 13.6 MB | 0.6 MB | 层级结构 + 主导词（按需加载） |
| `drg.json` | 14.9 MB | 0.4 MB | DRG分组数据 + MCC/CC列表 |

### 工具
| 文件 | 用途 |
|------|------|
| `tools/validate.py` | 验证 app.js 括号平衡 + HTML 引用完整性 |
| `server_gzip.py` | HTTP 服务器 (端口 8765)，对 .json 文件启用 gzip |

### 数据构建管道 (`_builder/`)
| 文件 | 用途 |
|------|------|
| `init_db.py` | 创建 SQLite 数据库结构 |
| `import_official.py` | 从 Excel 导入 ICD-10/ICD-9 医保版 |
| `import_clinical20.py` | 导入 ICD-10 医保版2.0 对照 |
| `import_icd9_clinical.py` | 导入 ICD-9 临床版3.0 对照 |
| `import_chs_drg.py` | 导入 CHS-DRG 2.0 分组方案 |
| `import_drg_dip.py` | 导入 DRG 详细表 + DIP |
| `build_icd10_hierarchy.py` | 构建 ICD-10 层级 |
| `build_icd9_hierarchy.py` | 构建 ICD-9 层级 |
| `import_lead_terms.py` | 导入 ICD-9 主导词 |
| `extract_cc_mcc.py` | 提取 MCC/CC 列表 |
| `extract_dip_pdf.py` | 从 PDF 提取 DIP 2.0 核心病种 |
| `extract_procedures.py` | 提取手术操作分类 |
| `fix_mdc_adrg.py` | 修复 MDC-ADRG 映射 |
| `generate_md.py` | 生成 Markdown 文档 |
| `generate_web_json.py` | **核心**: 从 SQLite 导出所有 JSON 数据文件 |

### 归档的临时脚本
`_archive/` — 23 个一次性诊断/修复脚本（已归档）
`web/_archive/` — 网页布局修复临时脚本

## 数据库 (icd_kb.db, 23 MB)
- `icd10_codes` / `icd10_sections` / `icd10_chapters`
- `icd10_clinical_map` — 医保版 ↔ 国临版 对照
- `icd10_hierarchy` — 6级层级（亚目→类目→节→章）
- `icd9_codes` / `icd9_chapters`
- `icd9_clinical_map` — 含类别、录入选项、不作为主手术
- `icd9_hierarchy` / `icd9_lead_terms`
- `drg_adrg` / `drg_groups` — DRG分组
- `adrg_diagnosis_map` / `adrg_procedure_map` — dx/px → ADRG
- `mcc_list` / `cc_list` / `cc_exclusions`
- `no_group_dx` / `no_group_px` — 不作为主诊/主手术
- `multitrauma_zones` — 多发伤区域
- `dip_groups` — DIP 2.0 核心病种

## JS 代码架构 (app.js)

### 全局数据
- `D` — `data.json` 完整数据（含 m10/m9 快速查找表）
- `_drg` — `drg.json` 数据（含 mccS/ccS Set、byMDC 索引、_linfenRW）

### 流程
1. **页面加载**: fetch data.json → fetch drg.json → 就绪
2. **ICD-10 搜索** (`s10`, `t10`): 从 `D.icd10` 筛选 → 按需加载 detail.json
3. **ICD-9 搜索** (`s9`, `t9`): 从 `D.icd9` 筛选 → 按需加载 detail.json
4. **DRG 分组** (`dr` → `pickBest` → `showAdrg`):
   - 诊断/手术输入 → 匹配 ADRG → MDC 决策
   - QY 歧义处理：手术优先规则
   - 性别过滤、MCC/CC 排除表计算
   - 临汾版本：权重 + 费率计算
5. **DIP 搜索** (`sd`): 从 `D.dip` 筛选显示

### 关键函数
| 函数 | 行数(拆分前) | 用途 |
|------|-------------|------|
| `dr()` | ~306-425 | DRG分组主逻辑（最复杂） |
| `showAdrg()` | ~348-367 | ADRG 渲染 |
| `pickBest()` | ~327-332 | MDC优先级选择 |
| `lookDx()` / `lookPx()` | ~311-312 | 编码查找 |
| `sdx()` / `spx()` | ~290-291 | 诊断/手术建议 |
| `rc()` | ~297-303 | 刷新已选标签 |

## 常见调试场景

### JS 语法错误定位
```bash
cd _builder/web && python3 tools/validate.py
```

### 括号不平衡排查
```bash
python3 -c "
import re
with open('app.js','r') as f: code=f.read()
clean=re.sub(r'\"[^\"]*\"', '\"\"', code)
clean=re.sub(r\"'[^']*'\", \"''\", clean)
clean=re.sub(r'//[^\n]*', '', clean)
opens=clean.count('{')
closes=clean.count('}')
print(f'{{: {opens}, }}: {closes}, diff: {opens-closes}')
"
```

### 启动开发服务器
```bash
cd _builder/web && python3 server_gzip.py
# 访问 http://localhost:8765
```
