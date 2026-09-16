---
tags:
  - dataview
  - examples
  - queries
created: 2026-06-18
---

# 🔍 Dataview 查询示例

> 使用 Dataview 插件查询和展示知识库内容的示例。

---

## 📊 基础统计查询

### 文件统计
```dataview
TABLE length(rows) as "文件数"
FROM ""
WHERE file.name != "_index" AND file.name != "README"
GROUP BY file.folder as "文件夹"
SORT length(rows) DESC
```

### 标签统计
```dataview
TABLE length(rows) as "使用次数"
FROM ""
WHERE file.tags
FLATTEN file.tags as tag
GROUP BY tag as "标签"
SORT length(rows) DESC
LIMIT 20
```

---

## 🏥 医疗编码查询

### ICD-10 章节概览
```dataview
TABLE 
  file.link as "章节",
  length(filter(file.outlinks, (x) => contains(string(x), "ICD10"))) as "链接数"
FROM "ICD10-疾病诊断"
WHERE contains(file.name, "_index")
SORT file.name ASC
```

### 常用诊断编码
```dataview
TABLE
  file.link as "编码",
  contains(file.tags, "#icd10") as "ICD-10",
  contains(file.tags, "#常用") as "常用"
FROM "速查手册/常见诊断编码速查"
SORT file.name ASC
```

---

## 📈 内容分析查询

### 最近更新的文件
```dataview
TABLE
  file.link as "文件",
  file.mtime as "修改时间",
  length(file.content) as "字数"
FROM ""
SORT file.mtime DESC
LIMIT 10
```

### 大文件列表
```dataview
TABLE
  file.link as "文件",
  round(length(file.content) / 1024, 1) as "大小(KB)",
  length(file.outlinks) as "出链数"
FROM ""
WHERE length(file.content) > 5000
SORT length(file.content) DESC
LIMIT 20
```

---

## 🔗 链接分析查询

### 孤立文件（无入链）
```dataview
TABLE
  file.link as "文件",
  length(file.inlinks) as "入链数"
FROM ""
WHERE length(file.inlinks) = 0 AND file.name != "_index"
SORT file.name ASC
LIMIT 20
```

### 热门文件（最多入链）
```dataview
TABLE
  file.link as "文件",
  length(file.inlinks) as "入链数",
  length(file.outlinks) as "出链数"
FROM ""
WHERE length(file.inlinks) > 0
SORT length(file.inlinks) DESC
LIMIT 20
```

---

## 🏷️ 标签相关查询

### 按标签分类的文件
```dataview
TABLE
  file.link as "文件",
  file.tags as "标签"
FROM ""
WHERE contains(file.tags, "#icd10")
SORT file.name ASC
```

### 标签网络
```dataview
TABLE
  tag as "标签",
  length(rows) as "使用次数"
FROM ""
FLATTEN file.tags as tag
GROUP BY tag
SORT length(rows) DESC
LIMIT 30
```

---

## 📊 代码块查询

### 包含代码块的文件
```dataview
TABLE
  file.link as "文件",
  length(filter(file.content, (x) => contains(x, "```"))) as "代码块数"
FROM ""
WHERE contains(file.content, "```")
SORT file.name ASC
```

---

## 🎯 高级查询示例

### 复合条件查询
```dataview
TABLE
  file.link as "文件",
  file.size as "大小",
  length(file.outlinks) as "出链数",
  length(file.inlinks) as "入链数"
FROM ""
WHERE 
  contains(file.tags, "#icd10") AND
  length(file.content) > 1000 AND
  length(file.outlinks) > 5
SORT length(file.inlinks) DESC
LIMIT 15
```

### 动态内容查询
```dataview
TABLE
  file.link as "文件",
  dateformat(file.ctime, "yyyy-MM-dd") as "创建时间",
  dateformat(file.mtime, "yyyy-MM-dd") as "修改时间",
  length(file.content) as "字数"
FROM ""
WHERE file.ctime >= date(today) - dur(30 days)
SORT file.ctime DESC
```

---

## 🔧 实用查询模板

### 知识库健康检查
```dataview
TABLE
  "总文件数" as "指标",
  length("") as "值"
FROM ""
UNION
TABLE
  "总字数" as "指标",
  sum(length(file.content)) as "值"
FROM ""
UNION
TABLE
  "总链接数" as "指标",
  sum(length(file.outlinks)) as "值"
FROM ""
```

### 待完善文件
```dataview
TABLE
  file.link as "文件",
  contains(file.tags, "#待完善") as "待完善",
  contains(file.tags, "#草稿") as "草稿"
FROM ""
WHERE 
  contains(file.tags, "#待完善") OR
  contains(file.tags, "#草稿")
SORT file.mtime ASC
```

---

## 📝 使用提示

1. **性能考虑**：大型知识库中避免复杂的 FLATTEN 操作
2. **索引优化**：定期重建 Dataview 索引
3. **标签一致性**：保持标签命名规范
4. **链接维护**：定期检查断开的链接

---

## 🔗 相关资源

- [Dataview 官方文档](https://blacksmithgu.github.io/obsidian-dataview/)
- [Dataview API 参考](https://blacksmithgu.github.io/obsidian-dataview/api/)
- [Dataview 示例集合](https://publish.obsidian.md/dataview/Examples)

---

**维护者**: Claudian AI Assistant  
**最后更新**: 2026-06-18