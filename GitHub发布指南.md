# ICD 编码知识库 - GitHub 发布指南

## 📊 项目概况

| 项目 | 详情 |
|------|------|
| 仓库名称 | ICD-KnowledgeBase |
| 主要文件 | `_builder/web/` 目录 |
| 数据大小 | 约 70 MB（json 文件） |
| 访问地址 | `http://localhost:8765/` |

---

## 🚀 发布步骤

### 第一步：在 GitHub 创建仓库

1. 打开浏览器访问：**https://github.com/new**
2. 填写仓库信息：
   ```
   Repository name: ICD-KnowledgeBase
   Description: ICD-10/ICD-9/CHS-DRG/DIP 编码查询知识库
   Visibility: Public（公开）
   ```
3. **不要勾选** "Add a README file"
4. 点击 **Create repository**

---

### 第二步：推送代码到 GitHub

打开 PowerShell 或 CMD，执行以下命令：

```powershell
# 1. 进入项目目录
cd D:\AI_libra\codex_Obsi

# 2. 添加远程仓库（替换 YOUR_USERNAME 为你的 GitHub 用户名）
git remote add origin https://github.com/YOUR_USERNAME/ICD-KnowledgeBase.git

# 3. 查看要提交的文件
git status

# 4. 只添加 Web 应用相关文件（排除大数据文件）
git add _builder/web/index.html
git add _builder/web/app.js
git add _builder/web/style.css
git add _builder/web/data.json
git add _builder/web/drg.json
git add _builder/web/detail.json
git add _builder/web/coding_rules.json
git add _builder/web/server_gzip.py
git add _builder/web/侵权声明.md
git add _builder/web/README_import_local.md
git add README.md
git add .gitignore

# 5. 提交更改
git commit -m "发布 ICD 编码知识库 v2.0

功能：
- ICD-10 诊断编码查询（33,304 条）
- ICD-9 手术操作查询（13,684 条）
- CHS-DRG 2.0 分组器（409 ADRG）
- DIP 2.0 病种匹配（9,520 病种）
- 编码转换工具

数据版权：国家医疗保障局公开数据"

# 6. 推送到 GitHub
git push -u origin master
```

---

### 第三步：启用 GitHub Pages

1. 在 GitHub 仓库页面，点击 **Settings** 标签
2. 左侧菜单选择 **Pages**
3. 配置：
   ```
   Source: Deploy from a branch
   Branch: master
   Folder: / (root)
   ```
4. 点击 **Save**
5. 等待 1-2 分钟，访问：
   ```
   https://YOUR_USERNAME.github.io/ICD-KnowledgeBase/
   ```

---

## ⚠️ 重要提示

### 文件排除说明

以下文件已被 `.gitignore` 排除，不会上传：
- `*.json.gz`（压缩版本）
- 临时文件（`nul`, `test.html` 等）
- 构建脚本

### 数据文件大小

| 文件 | 大小 | 说明 |
|------|------|------|
| data.json | 11 MB | ICD-10/ICD-9/DIP 数据 |
| drg.json | 16 MB | CHS-DRG 2.0 数据 |
| detail.json | 14 MB | 详情数据 |
| coding_rules.json | 4 MB | 编码规则 |

**总计约 45 MB**，在 GitHub 免费限额内。

---

## 🔧 本地运行（开发用）

```powershell
# 进入 web 目录
cd D:\AI_libra\codex_Obsi\_builder\web

# 启动服务器
python server_gzip.py

# 访问 http://localhost:8765/
```

---

## 📖 使用说明

详见项目根目录的 [README.md](./README.md)

---

## 📝 更新流程

当需要更新数据时：

```powershell
# 1. 修改数据文件后
git add _builder/web/data.json
git add _builder/web/drg.json
# ... 其他修改

# 2. 提交并推送
git commit -m "更新数据：xxx"
git push
```

---

**祝你发布顺利！** 🎉
