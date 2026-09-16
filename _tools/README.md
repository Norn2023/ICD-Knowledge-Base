# 🔧 知识库优化工具使用指南

> 本指南介绍如何使用提供的工具来优化和管理你的 Obsidian 知识库。

---

## 📁 工具目录结构

```
_tools/
├── link_checker.py          # 链接检查和修复工具
├── knowledge_graph.py       # 知识图谱生成工具
├── advanced_search.py       # 高级搜索工具
└── README.md               # 本文件
```

---

## 🔗 1. 链接检查工具

### 功能
- 扫描所有 Markdown 文件中的链接
- 检测断开的链接
- 提供修复建议
- 支持批量修复

### 使用方法

```bash
# 检查链接
python _tools/link_checker.py --vault-path .

# 检查并修复链接
python _tools/link_checker.py --vault-path . --fix

# 生成详细报告
python _tools/link_checker.py --vault-path . --output link_report.json
```

### 输出示例
```
📊 链接检查报告:
  总文件数: 150
  总链接数: 1200
  有效链接: 1180
  断开链接: 20
  成功率: 98.3%
```

---

## 🕸️ 2. 知识图谱工具

### 功能
- 扫描整个知识库构建关系图
- 生成 Mermaid 格式的可视化图谱
- 导出 JSON 格式的图谱数据
- 提供统计分析

### 使用方法

```bash
# 生成 Mermaid 图谱
python _tools/knowledge_graph.py --vault-path . --format mermaid

# 导出 JSON 数据
python _tools/knowledge_graph.py --vault-path . --format json

# 同时生成两种格式
python _tools/knowledge_graph.py --vault-path . --output my_graph
```

### 查看图谱
生成的 `knowledge_graph.md` 文件可以在 Obsidian 中直接打开，Mermaid 图谱会自动渲染。

---

## 🔍 3. 高级搜索工具

### 搜索类型

| 类型 | 说明 | 示例 |
|------|------|------|
| `exact` | 精确匹配 | `python advanced_search.py --query "心肌梗死" --type exact` |
| `fuzzy` | 模糊匹配 | `python advanced_search.py --query "心梗" --type fuzzy` |
| `semantic` | 语义搜索 | `python advanced_search.py --query "心脏病" --type semantic` |
| `tag` | 标签搜索 | `python advanced_search.py --query "icd10" --type tag` |
| `link` | 链接搜索 | `python advanced_search.py --query "ICD10-疾病诊断/_index" --type link` |
| `content` | 内容搜索（正则） | `python advanced_search.py --query "糖尿病.*肾病" --type content` |

### 使用示例

```bash
# 模糊搜索
python _tools/advanced_search.py --query "心脏" --type fuzzy --limit 10

# 语义搜索
python _tools/advanced_search.py --query "心梗" --type semantic

# 搜索所有标签为 icd10 的文件
python _tools/advanced_search.py --query "icd10" --type tag

# 使用正则表达式搜索内容
python _tools/advanced_search.py --query "A0[0-9]\.\d{3}" --type content

# 显示搜索索引统计
python _tools/advanced_search.py --query "" --stats
```

---

## 🚀 快速开始

### 1. 首次使用

```bash
# 进入工具目录
cd _tools

# 运行链接检查
python link_checker.py --vault-path ..

# 生成知识图谱
python knowledge_graph.py --vault-path .. --output ../00-导航/知识图谱

# 构建搜索索引并测试
python advanced_search.py --vault-path .. --query "编码规则" --type fuzzy
```

### 2. 日常维护

```bash
# 每周执行一次链接检查
python _tools/link_checker.py --vault-path . --fix

# 每月更新知识图谱
python _tools/knowledge_graph.py --vault-path . --output 00-导航/知识图谱
```

---

## 📊 输出文件说明

### 链接检查报告
- `link_check_report.json`: 包含所有断开链接的详细信息

### 知识图谱
- `knowledge_graph.md`: Mermaid 格式的可视化图谱
- `knowledge_graph.json`: JSON 格式的图谱数据（包含节点和边）

### 搜索结果
- 可以通过 `--output` 参数将搜索结果保存为 JSON 文件

---

## 🔧 故障排除

### 常见问题

1. **Python 版本问题**
   - 确保使用 Python 3.7+
   - 运行 `python --version` 检查

2. **编码问题**
   - 确保文件使用 UTF-8 编码
   - 工具已内置 UTF-8 支持

3. **路径问题**
   - 使用相对路径或绝对路径
   - Windows 用户使用正斜杠 `/` 或双反斜杠 `\\`

4. **Mermaid 渲染问题**
   - 确保 Obsidian 安装了 Mermaid 插件
   - 或者使用在线 Mermaid 编辑器查看

---

## 📈 性能优化建议

### 大型知识库（>1000 文件）
1. 使用 `--limit` 参数限制搜索结果数量
2. 定期清理不需要的文件
3. 使用标签系统组织文件

### 搜索优化
1. 建立清晰的标签体系
2. 使用有意义的文件名
3. 保持链接的一致性

---

## 🤝 贡献

如果你发现 bug 或有改进建议，请：
1. 记录问题
2. 提供复现步骤
3. 提交修复方案

---

## 📝 更新日志

### v1.0 (2026-06-18)
- 初始版本发布
- 支持链接检查和修复
- 支持知识图谱生成
- 支持多种搜索类型

---

**维护者**: Claudian AI Assistant  
**最后更新**: 2026-06-18