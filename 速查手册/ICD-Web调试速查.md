---
title: "ICD知识库Web调试速查"
tags: [icd, web, debug, tool]
created: 2026-06-19
---

## 快速命令

### 启动服务器
```bash
cd _builder/web && python3 server_gzip.py
# → http://localhost:8765
```

### 验证 JS 语法
```bash
# 方法1: 完整验证（括号 + 引用 + 数据文件）
cd _builder/web && python3 tools/validate.py

# 方法2: 仅括号检查
cd _builder/web && python3 tools/bcheck.py

# 方法3: Node.js 语法检查
node -e "new Function(require('fs').readFileSync('_builder/web/app.js','utf-8'))"
```

### 安全的文本替换
```bash
cd _builder/web

# 预览变更（不实际修改）
python3 tools/patch.py '旧代码片段' '新代码片段' --dry-run

# 执行替换（自动备份 app.js）
python3 tools/patch.py '旧代码片段' '新代码片段'
```

### JSON 数据重新生成
```bash
cd _builder && python3 generate_web_json.py
# 自动生成: web/data.json, web/detail.json, web/drg.json
# 并自动 gzip 压缩为 .gz 文件（compresslevel=9）
```

### DIP 数据重新提取
```bash
cd _builder && python3 extract_dip_pdf.py
```

---

## 调试常见问题

### 场景A: 页面空白/不加载
**原因**: JS 语法错误导致整个脚本解析失败
**排查**:
```bash
cd _builder/web && python3 tools/bcheck.py
# 如果 FAIL，看哪个括号多了/少了
# 进一步定位: 看 app.js 的 dr() 函数区域(后半部分)
```

### 场景B: DRG分组器不工作
**原因**: `drg.json` 未加载或数据结构不对
**排查**:
1. 打开浏览器 F12 → Console 看报错
2. 检查 `drg.json` 是否存在：`ls -la _builder/web/drg.json.gz`
3. 检查服务端 gzip 是否正确：`curl -I http://localhost:8765/drg.json`

### 场景C: 搜索无结果
**原因**: data.json 未加载或数据为空
**排查**: F12 Console 输入 `D.icd10.length` 看是否 > 0

### 场景D: 修改 JS 后功能异常
**原因**: 括号不匹配、变量未声明、作用域问题
**排查**:
1. 先跑 `python3 tools/validate.py`
2. 检查浏览器 Console 的错误行号，对应 app.js 行号
3. 变量作用域：确认 `var` 声明在正确的函数层级

---

## 关键文件速查

| 文件 | 路径 | 何时修改 |
|------|------|----------|
| HTML结构 | `_builder/web/index.html` | 添加导航/标签页 |
| CSS样式 | `_builder/web/style.css` | 调整外观 |
| JS逻辑 | `_builder/web/app.js` | **最常修改** |
| 数据导出 | `_builder/generate_web_json.py` | 数据库结构变了 |
| 服务器 | `_builder/web/server_gzip.py` | 调整端口/缓存 |
| 工具 | `_builder/web/tools/*.py` | 不要修改 |

### app.js 函数地图
```
变量声明 (行1-12)
  st()          — 标签切换
  s10(), t10()  — ICD-10搜索/详情
  s9(), t9()    — ICD-9搜索/详情
  f10(), f9()   — DRG输入建议
  sdx(), spx()  — 诊断/手术输入处理
  adx(), apx()  — 添加诊断/手术
  rc()          — 刷新标签
  calAge(), dr()— 年龄计算 + DRG分组核心
    lookDx()    — 诊断→ADRG查找
    lookPx()    — 手术→ADRG查找
    pickBest()  — MDC优先级决策
    showAdrg()  — ADRG渲染(含临汾权重)
  sd()          — DIP搜索
  DOM事件绑定   — (末尾)
```

---

## 文件体积参考

| 文件 | 大小 | 说明 |
|------|------|------|
| app.js | 34 KB | JS逻辑 |
| index.html | 7 KB | HTML骨架 |
| style.css | 7 KB | 样式 |
| data.json.gz | 1.2 MB | 通过网络传输 |
| detail.json.gz | 0.6 MB | 按需加载 |
| drg.json.gz | 0.4 MB | 预加载 |

**总传输量**: ~2.2 MB (gzip) — 首次加载

---

## 架构参考
详见: [[速查手册/ICD知识库Web应用-架构]]
