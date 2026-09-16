#!/usr/bin/env python3
"""
中英文医学文献导入管线
用法：
  # PubMed 搜索并自动导入（加 --download-pdf 自动下载开放获取全文）
  python import_literature.py pubmed --query "covid-19 treatment" --max 50
  python import_literature.py pubmed --query "covid-19 treatment" --max 50 --download-pdf

  # 导入本地 PDF（拖拽文件夹）
  python import_literature.py pdf --dir ./my_papers

  # 查看文献统计
  python import_literature.py stats

  # 导出文献为 JSON（供 Web App 使用）
  python import_literature.py export --out ./literature
"""

import sqlite3, os, sys, json, re, time, hashlib, urllib.parse, xml.etree.ElementTree as ET
from datetime import datetime

# Windows GBK 编码兼容
if sys.platform == "win32" and sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DB_PATH = os.path.join(os.path.dirname(__file__), "icd_kb.db")
LIT_DIR = os.path.join(os.path.dirname(__file__), "literature")
os.makedirs(LIT_DIR, exist_ok=True)

NCBI_EMAIL = "your_email@example.com"  # NCBI 要求提供邮箱
NCBI_API_KEY = ""                       # 可选，有 key 提高 QPS 到 10/秒

# OpenAlex API 配置（用于 OA 文章 PDF 发现）
# 免费注册 API Key: https://openalex.org/settings/api
# 免费额度：每天 100 次 PDF 下载 + 无限次元数据查询
OPENALEX_API_KEY = os.environ.get("OPENALEX_API_KEY", "")


# ══════════════════════════════════════════════════════════════
# 数据库操作
# ══════════════════════════════════════════════════════════════

def get_db():
    if not os.path.exists(DB_PATH):
        print(f"数据库不存在: {DB_PATH}")
        sys.exit(1)
    return sqlite3.connect(DB_PATH)


# ══════════════════════════════════════════════════════════════
# PubMed E-utilities API（无需 Biopython）
# ══════════════════════════════════════════════════════════════

def ncbi_request(url, params, max_retries=3):
    """带重试的 NCBI API 请求"""
    import requests
    params['email'] = NCBI_EMAIL
    if NCBI_API_KEY:
        params['api_key'] = NCBI_API_KEY
    for attempt in range(max_retries):
        try:
            r = requests.get(url, params=params, timeout=30)
            r.raise_for_status()
            return r
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(1.5 ** attempt)
            else:
                print(f"  ✗ API 请求失败: {e}")
                return None

def search_pubmed(query, max_results=20):
    """搜索 PubMed 返回 PMID 列表"""
    print(f"  PubMed 搜索: '{query}' (最多 {max_results} 篇)")
    r = ncbi_request("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi", {
        "db": "pubmed", "term": query, "retmax": max_results, "retmode": "json"
    })
    if not r:
        return []
    data = r.json()
    ids = data.get("esearchresult", {}).get("idlist", [])
    total = data.get("esearchresult", {}).get("count", "0")
    print(f"  共找到 {total} 篇，本次获取 {len(ids)} 篇")
    return ids

def fetch_details(pmids):
    """根据 PMID 列表获取文献详细信息"""
    if not pmids:
        return []
    pmids_str = ",".join(pmids)
    r = ncbi_request("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi", {
        "db": "pubmed", "id": pmids_str, "retmode": "xml"
    })
    if not r:
        return []
    return parse_pubmed_xml(r.text)

def parse_pubmed_xml(xml_text):
    """解析 PubMed XML 返回文献字典列表"""
    articles = []
    root = ET.fromstring(xml_text)
    for article_elem in root.iter("PubmedArticle"):
        try:
            art = _parse_one_article(article_elem)
            if art:
                articles.append(art)
        except Exception as e:
            continue
    return articles

def _parse_one_article(elem):
    medline = elem.find(".//MedlineCitation")
    if medline is None:
        return None

    pmid = medline.findtext("PMID", "")
    article = medline.find("Article")
    if article is None:
        return None

    title = article.findtext("ArticleTitle", "")
    if not title:
        return None

    lang = "en"
    lang_elem = article.find("Language")
    if lang_elem is not None and lang_elem.text:
        lang = lang_elem.text.lower()

    abstract_parts = article.findall(".//AbstractText")
    abstract = " ".join([(a.text or "") for a in abstract_parts])

    authors = []
    author_list = article.find("AuthorList")
    if author_list is not None:
        for author in author_list.findall("Author"):
            last = author.findtext("LastName", "")
            fore = author.findtext("ForeName", "")
            if last or fore:
                authors.append(f"{last} {fore}".strip())

    journal_elem = article.find("Journal")
    journal = ""
    year = 0
    if journal_elem is not None:
        journal = journal_elem.findtext("Title", "") or journal_elem.findtext("ISOAbbreviation", "")
        pub_date = journal_elem.find(".//PubDate")
        if pub_date is not None:
            y = pub_date.findtext("Year", "")
            if y:
                year = int(y)

    keywords = []
    kw_list = medline.find(".//KeywordList")
    if kw_list is not None:
        keywords = [k.text for k in kw_list.findall("Keyword") if k.text]

    doi = ""
    pmc_id = ""
    # 只从 PubmedData/ArticleIdList 中取（避免从参考文献列表误取）
    for e_id in elem.findall("PubmedData/ArticleIdList/ArticleId"):
        if e_id.get("IdType") == "doi":
            doi = e_id.text or ""
        if e_id.get("IdType") == "pmc":
            pmc_id = (e_id.text or "").strip()

    return {
        "pmid": pmid,
        "pmc_id": pmc_id,
        "title": title,
        "title_cn": None,
        "authors": json.dumps(authors, ensure_ascii=False),
        "journal": journal or "",
        "year": year,
        "doi": doi,
        "abstract": abstract,
        "full_text": None,
        "keywords": json.dumps(keywords, ensure_ascii=False),
        "lang": lang,
        "source": "PubMed",
        "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else "",
    }


# ══════════════════════════════════════════════════════════════
# 本地 PDF 导入
# ══════════════════════════════════════════════════════════════

def import_pdf(filepath):
    """导入单个 PDF 文件"""
    try:
        import fitz
    except ImportError:
        print("需要安装 PyMuPDF: pip install PyMuPDF")
        return None

    basename = os.path.basename(filepath)
    print(f"  解析: {basename}")

    try:
        doc = fitz.open(filepath)
    except Exception as e:
        print(f"  ✗ 无法打开 PDF: {e}")
        return None

    # 提取全文
    full_text = ""
    for page in doc:
        full_text += page.get_text()

    if not full_text.strip():
        print(f"  ⚠ 未提取到文本（可能是扫描件，需要 OCR）")
        doc.close()
        return None

    # 从文本中启发式提取标题（通常是第一页前几行）
    lines = [l.strip() for l in full_text.split("\n") if l.strip()]
    title = basename.replace(".pdf", "").strip()

    # 尝试从第一页找标题（跳过页眉页码等短行）
    title_candidates = []
    for line in lines[:30]:
        clean = re.sub(r'^\d+\s*$', '', line).strip()
        if len(clean) > 15 and len(clean) < 500:
            title_candidates.append(clean)

    if title_candidates:
        # 用最长的非空行做标题
        longest = max(title_candidates, key=len)
        if len(longest) > len(title):
            title = longest

    # 复制 PDF 到 literature 目录
    import shutil
    dest = os.path.join(LIT_DIR, basename)
    shutil.copy2(filepath, dest)

    doc.close()
    return {
        "pmid": None,
        "title": title,
        "title_cn": None,
        "authors": None,
        "journal": None,
        "year": None,
        "doi": None,
        "abstract": None,
        "full_text": full_text,
        "keywords": None,
        "lang": "zh" if any('\u4e00' <= c <= '\u9fff' for c in title) else "en",
        "source": "本地PDF",
        "url": None,
        "pdf_path": basename,
    }


# ══════════════════════════════════════════════════════════════
# PMC 开放获取 PDF 自动下载
# ══════════════════════════════════════════════════════════════

def try_get_pmc_id(article):
    """从文章字典中获取 PMCID（保持原样，如 'PMC123456'）"""
    pmc = article.get("pmc_id", "") or ""
    pmc = pmc.strip()
    return pmc if pmc else None


def get_pmc_oa_info(pmc_id):
    """通过 PMC OA API 查询开放获取文章的下载地址"""
    import requests, xml.etree.ElementTree as ET

    url = "https://www.ncbi.nlm.nih.gov/pmc/utils/oa/oa.fcgi"
    try:
        r = requests.get(url, params={"id": pmc_id}, timeout=15,
                         headers={"User-Agent": "Mozilla/5.0"})
        if r.status_code != 200:
            return None
        root = ET.fromstring(r.text)
        for link in root.iter("link"):
            fmt = link.get("format", "")
            href = link.get("href", "")
            if href.startswith("ftp://"):
                # OA 包路径已迁移到 deprecated/ 下
                href = href.replace("/pub/pmc/", "/pub/pmc/deprecated/")
            if fmt in ("pdf", "tgz"):
                return (fmt, href)
        return None
    except Exception as e:
        return None


def parse_nxml_text(source):
    """从 NXML (PMC XML) 中提取纯文本，支持文件路径或 BytesIO"""
    try:
        tree = ET.parse(source)
        root = tree.getroot()
        paragraphs = []
        for elem in root.iter():
            if elem.tag.endswith("p") or elem.tag.endswith("title"):
                text = "".join(elem.itertext()).strip()
                if text:
                    paragraphs.append(text)
        return "\n\n".join(paragraphs)
    except Exception:
        return None


def download_pmc_article(pmc_id, save_dir, pmid=""):
    """通过 PMC OA API 获取开放获取全文（PDF 或 NXML）"""
    import requests, tarfile, io
    from ftplib import FTP

    oa_info = get_pmc_oa_info(pmc_id)
    if not oa_info:
        return None

    fmt, oa_url = oa_info

    def _download_http(url):
        r = requests.get(url, timeout=60, allow_redirects=True,
                         headers={"User-Agent": "Mozilla/5.0"})
        if r.status_code == 200:
            return r.content
        return None

    def _download_ftp(ftp_url):
        """通过 FTP 下载文件"""
        # ftp://ftp.ncbi.nlm.nih.gov/pub/pmc/deprecated/oa_package/2b/74/PMC13370313.tar.gz
        parts = ftp_url.replace("ftp://", "").split("/", 1)
        if len(parts) != 2:
            return None
        server, path = parts
        try:
            ftp = FTP(server)
            ftp.login()
            data = io.BytesIO()
            ftp.retrbinary(f"RETR {path}", data.write)
            ftp.quit()
            return data.getvalue()
        except Exception:
            return None

    # 先尝试 HTTPS（将 ftp:// 转为 https://），失败后改用 FTP
    content = None
    http_url = oa_url
    if http_url.startswith("ftp://"):
        http_url = "https://" + http_url[6:]
    if http_url.startswith("https://"):
        content = _download_http(http_url)
    if content is None:
        content = _download_ftp(oa_url)

    if content is None or len(content) < 1000:
        return None

    # 是 TGZ 包，解压提取
    if fmt == "tgz" or content[:2] == b'\x1f\x8b':
        try:
            with tarfile.open(fileobj=io.BytesIO(content)) as tar:
                # 优先找 PDF
                pdf_members = [m for m in tar.getmembers()
                               if m.name.endswith(".pdf")]
                if pdf_members:
                    pdf_data = tar.extractfile(pdf_members[0]).read()
                    fname = f"{pmid or pmc_id}.pdf"
                    save_path = os.path.join(save_dir, fname)
                    with open(save_path, "wb") as f:
                        f.write(pdf_data)
                    print(f"    ✔ PDF: {fname} ({len(pdf_data) / 1024:.0f} KB)")
                    return ("pdf", save_path)

                # 没有 PDF，找 NXML 提取全文
                nxml_members = [m for m in tar.getmembers()
                                if m.name.endswith(".nxml")]
                if nxml_members:
                    nxml_data = tar.extractfile(nxml_members[0]).read()
                    full_text = parse_nxml_text(io.BytesIO(nxml_data))
                    fname = f"{pmid or pmc_id}.nxml"
                    save_path = os.path.join(save_dir, fname)
                    with open(save_path, "wb") as f:
                        f.write(nxml_data)
                    if full_text:
                        print(f"    ✔ NXML 全文已提取 ({len(full_text) / 1024:.0f} KB)")
                        return ("nxml", save_path, full_text)
        except Exception:
            return None
        return None

    # 是直接 PDF
    if content[:4] == b'%PDF':
        fname = f"{pmid or pmc_id}.pdf"
        save_path = os.path.join(save_dir, fname)
        with open(save_path, "wb") as f:
            f.write(content)
        print(f"    ✔ PDF: {fname} ({len(content) / 1024:.0f} KB)")
        return ("pdf", save_path)

    return None


def extract_pdf_text(pdf_path):
    """提取 PDF 全文文本"""
    try:
        import fitz
    except ImportError:
        return None
    try:
        doc = fitz.open(pdf_path)
        full_text = ""
        for page in doc:
            full_text += page.get_text()
        doc.close()
        return full_text if full_text.strip() else None
    except Exception:
        return None


def update_article_full_text(pmid, full_text, pdf_path):
    """更新数据库中已有文献的全文和 PDF 路径"""
    conn = get_db()
    try:
        conn.execute(
            "UPDATE literature SET full_text=?, pdf_path=?, updated_at=CURRENT_TIMESTAMP WHERE pmid=?",
            (full_text, pdf_path, pmid)
        )
        conn.commit()
        affected = conn.total_changes
        conn.close()
        return affected > 0
    except Exception as e:
        conn.close()
        return False


# ══════════════════════════════════════════════════════════════
# Sci-Hub 下载（付费文章兜底）
# ══════════════════════════════════════════════════════════════

SCI_HUB_DOMAINS = [
    "https://sci-hub.al",
    "https://sci-hub.red",
    "https://sci-hub.box",
    "https://sci-hub.st",
    "https://sci-hub.ru",
]


def download_from_scihub(doi, save_dir, pmid=""):
    """通过 Sci-Hub 下载付费文章的 PDF"""
    import requests, re

    for domain in SCI_HUB_DOMAINS:
        url = f"{domain}/{doi}"
        try:
            r = requests.get(url, timeout=20, allow_redirects=True,
                             headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
            if r.status_code != 200:
                continue

            html = r.text
            # 找 embed 标签中的 PDF URL
            embed_src = re.search(r'<embed[^>]+src=["\']([^"\']+)["\']', html)
            if not embed_src:
                continue

            pdf_url = embed_src.group(1)
            if pdf_url.startswith("//"):
                pdf_url = "https:" + pdf_url

            # 下载 PDF
            r2 = requests.get(pdf_url, timeout=60, allow_redirects=True,
                              headers={"User-Agent": "Mozilla/5.0"})
            if r2.status_code == 200 and r2.content[:4] == b'%PDF':
                fname = f"{pmid or doi.replace('/', '_')}.pdf"
                save_path = os.path.join(save_dir, fname)
                with open(save_path, "wb") as f:
                    f.write(r2.content)
                print(f"    ✔ Sci-Hub 下载: {fname} ({len(r2.content) / 1024:.0f} KB)")
                return save_path
        except Exception:
            continue
    return None


def download_oa_pdfs(articles):
    """自动下载全文：PMC OA 优先 → OpenAlex OA 链接 → Sci-Hub 兜底"""
    print("\n  --- 检查全文 ---")
    downloaded = 0
    for art in articles:
        pmid = art.get("pmid", "")
        doi = art.get("doi", "")
        title_short = art.get("title", "")[:50]
        print(f"  PMID {pmid}: {title_short}...")

        result = None
        source = ""

        # 方法1: PMC 开放获取
        pmc_id = try_get_pmc_id(art)
        if pmc_id:
            result = download_pmc_article(pmc_id, LIT_DIR, pmid)
            if result:
                source = "PMC OA"

        # 方法2: OpenAlex OA 链接发现（无需 API Key，从 OA locations/oa_url 尝试下载）
        if not result and doi:
            openalex_pdf = download_from_openalex(doi, LIT_DIR, pmid)
            if openalex_pdf:
                full_text = extract_pdf_text(openalex_pdf)
                if full_text:
                    pdf_basename = os.path.basename(openalex_pdf)
                    if update_article_full_text(pmid, full_text, pdf_basename):
                        downloaded += 1
                        print(f"    ✔ 全文已入库 (OpenAlex OA)")
                    continue

        # 方法3: Sci-Hub 兜底（有 DOI 且前两步没找到）
        if not result and doi:
            pdf_path = download_from_scihub(doi, LIT_DIR, pmid)
            if pdf_path:
                full_text = extract_pdf_text(pdf_path)
                if full_text:
                    pdf_basename = os.path.basename(pdf_path)
                    if update_article_full_text(pmid, full_text, pdf_basename):
                        downloaded += 1
                        print(f"    ✔ 全文已入库 (Sci-Hub)")
                continue

        if not result:
            print(f"    → 无全文可用")
            continue

        # 处理 PMC OA 结果（PDF 或 NXML）
        fmt = result[0]
        if fmt == "pdf":
            pdf_path = result[1]
            full_text = extract_pdf_text(pdf_path)
            if not full_text:
                print(f"    ⚠ 未能提取文本（可能为扫描件）")
                continue
        elif fmt == "nxml":
            pdf_path = result[1]
            full_text = result[2]
        else:
            continue

        pdf_basename = os.path.basename(pdf_path)
        if update_article_full_text(pmid, full_text, pdf_basename):
            downloaded += 1
            print(f"    ✔ 全文已入库 ({source})")

    if downloaded:
        print(f"\n  ✔ 共下载并入库 {downloaded} 篇全文")
    else:
        print(f"  （本次未找到可下载的全文）")


# ══════════════════════════════════════════════════════════════
# OpenAlex OA PDF 发现与下载
# ══════════════════════════════════════════════════════════════

def query_openalex(doi):
    """查询 OpenAlex API 获取文章 OA 信息（免费，无需 API Key）"""
    import requests
    try:
        r = requests.get(
            f"https://api.openalex.org/works/doi:{doi}",
            timeout=10,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        )
        if r.status_code != 200:
            return None
        return r.json()
    except Exception:
        return None


def download_from_openalex(doi, save_dir, pmid=""):
    """通过 OpenAlex 发现的 OA 链接下载 PDF（无需 API Key）
    
    三阶段策略：
    1. 从所有 OA location 的 pdf_url 尝试下载
    2. 从 primary oa_url 尝试下载
    3. 如用户配置了 API Key，尝试 OpenAlex 内容缓存 API
    """
    import requests

    data = query_openalex(doi)
    if not data:
        return None

    oa = data.get("open_access", {})
    is_oa = oa.get("is_oa", False)
    oa_url = oa.get("oa_url", "")
    oa_status = oa.get("oa_status", "")

    if not is_oa:
        return None  # 非 OA 文章，无法通过开放渠道获取

    # 收集所有 OA location 的 PDF URL
    candidates = []
    for loc in data.get("locations", []):
        if loc.get("is_oa") and loc.get("pdf_url"):
            pdf = loc["pdf_url"]
            if pdf not in candidates:
                candidates.append(pdf)

    # 补充 primary oa_url
    if oa_url and oa_url not in candidates:
        candidates.append(oa_url)

    # 如用户配置了 API Key，尝试 OpenAlex Content API（缓存 PDF，不会被封锁）
    if OPENALEX_API_KEY:
        oa_id = data.get("id", "")
        if oa_id:
            content_url = f"https://content.openalex.org/works/{oa_id}.pdf?api_key={OPENALEX_API_KEY}"
            candidates.append(content_url)

    if not candidates:
        return None

    print(f"    → OpenAlex: {len(candidates)} 个候选 URL (OA类型={oa_status})")

    for pdf_url in candidates:
        try:
            r = requests.get(pdf_url, timeout=30, allow_redirects=True,
                             headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
            if r.status_code == 200 and len(r.content) > 1000 and r.content[:4] == b'%PDF':
                fname = f"{pmid or doi.replace('/', '_')}_oa.pdf"
                save_path = os.path.join(save_dir, fname)
                with open(save_path, "wb") as f:
                    f.write(r.content)
                print(f"    ✔ OpenAlex 下载: {fname} ({len(r.content) / 1024:.0f} KB)")
                return save_path
            else:
                # 简短记录失败的 URL
                short_url = pdf_url.rsplit("/", 1)[-1][:40]
                print(f"    →   {short_url}... HTTP {r.status_code}")
        except Exception as e:
            short_url = pdf_url.rsplit("/", 1)[-1][:40]
            print(f"    →   {short_url}... {str(e)[:50]}")
            continue

    return None


# ══════════════════════════════════════════════════════════════
# 入库
# ══════════════════════════════════════════════════════════════

def save_to_db(articles):
    """将文献写入 SQLite 数据库（重复跳过）"""
    conn = get_db()
    c = conn.cursor()
    new_count = 0
    for art in articles:
        try:
            c.execute("""
                INSERT OR IGNORE INTO literature
                (pmid, pmc_id, title, title_cn, authors, journal, year, doi,
                 abstract, full_text, keywords, lang, source, url, pdf_path)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (
                art.get("pmid"), art.get("pmc_id"), art.get("title"), art.get("title_cn"),
                art.get("authors"), art.get("journal"), art.get("year"),
                art.get("doi"), art.get("abstract"), art.get("full_text"),
                art.get("keywords"), art.get("lang"), art.get("source"),
                art.get("url"), art.get("pdf_path"),
            ))
            if c.rowcount:
                new_count += 1
        except Exception as e:
            print(f"  ✗ 入库失败: {art.get('title', '')[:40]}... {e}")
    conn.commit()
    conn.close()
    return new_count


# ══════════════════════════════════════════════════════════════
# JSON 导出（供 Web App 使用）
# ══════════════════════════════════════════════════════════════

def export_json(out_dir=None):
    """导出文献为 JSON 文件"""
    if out_dir is None:
        out_dir = os.path.join(os.path.dirname(__file__), "literature")
    os.makedirs(out_dir, exist_ok=True)

    conn = get_db()
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM literature ORDER BY year DESC").fetchall()
    conn.close()

    records = []
    for r in rows:
        authors_raw = r["authors"] if r["authors"] else "[]"
        kw_raw = r["keywords"] if r["keywords"] else "[]"
        records.append({
            "id": r["id"],
            "pmid": r["pmid"],
            "title": r["title"],
            "title_cn": r["title_cn"],
            "authors": json.loads(authors_raw) if isinstance(authors_raw, str) else [],
            "journal": r["journal"],
            "year": r["year"],
            "doi": r["doi"],
            "abstract": r["abstract"],
            "keywords": json.loads(kw_raw) if isinstance(kw_raw, str) else [],
            "lang": r["lang"],
            "source": r["source"],
            "url": r["url"],
        })

    out_path = os.path.join(out_dir, "literature.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

    # 生成精简搜索索引
    search_index = []
    for r in records:
        search_index.append({
            "i": r["id"],
            "t": r["title"],
            "a": r["authors"],
            "j": r["journal"],
            "y": r["year"],
            "l": r["lang"],
        })

    idx_path = os.path.join(out_dir, "search_index.json")
    with open(idx_path, "w", encoding="utf-8") as f:
        json.dump(search_index, f, ensure_ascii=False)

    print(f"✓ 导出 {len(records)} 篇文献到:")
    print(f"  {out_path} ({os.path.getsize(out_path) / 1024:.0f} KB)")
    print(f"  {idx_path} ({os.path.getsize(idx_path) / 1024:.0f} KB)")
    return records


# ══════════════════════════════════════════════════════════════
# 统计
# ══════════════════════════════════════════════════════════════

def show_stats():
    conn = get_db()
    total = conn.execute("SELECT COUNT(*) FROM literature").fetchone()[0]
    by_lang = conn.execute("SELECT lang, COUNT(*) FROM literature GROUP BY lang").fetchall()
    by_source = conn.execute("SELECT source, COUNT(*) FROM literature GROUP BY source").fetchall()
    years = conn.execute("SELECT year, COUNT(*) FROM literature WHERE year IS NOT NULL GROUP BY year ORDER BY year DESC").fetchall()
    conn.close()

    print(f"\n{'='*50}")
    print(f"  文献库统计")
    print(f"{'='*50}")
    print(f"  总计: {total} 篇")
    print(f"  语言分布:")
    for lang, cnt in by_lang:
        print(f"    {lang}: {cnt} 篇")
    print(f"  来源分布:")
    for src, cnt in by_source:
        print(f"    {src}: {cnt} 篇")
    if years:
        print(f"  年份分布 (最近5年):")
        for y, cnt in years[:5]:
            print(f"    {y}: {cnt} 篇")


# ══════════════════════════════════════════════════════════════
# CLI 入口
# ══════════════════════════════════════════════════════════════

def cmd_stats():
    show_stats()

def cmd_pubmed(args):
    query = args.get("--query") or " ".join(args.get("_extra", []))
    if not query:
        print("请指定搜索词: --query \"covid-19 treatment\"")
        return
    max_results = int(args.get("--max", 20))
    pmids = search_pubmed(query, max_results)
    if not pmids:
        print("未找到文献")
        return
    articles = fetch_details(pmids)
    print(f"  获取到 {len(articles)} 篇文献详情")
    n = save_to_db(articles)
    print(f"✓ 新增 {n} 篇文献（{len(articles) - n} 篇已存在）")

    # 自动下载开放获取全文
    if args.get("--download-pdf"):
        download_oa_pdfs(articles)

    export_json()

def cmd_pdf(args):
    dir_path = args.get("--dir")
    if not dir_path:
        print("请指定 PDF 文件夹: --dir ./papers")
        return
    if not os.path.isdir(dir_path):
        print(f"目录不存在: {dir_path}")
        return
    pdfs = [f for f in os.listdir(dir_path) if f.lower().endswith(".pdf")]
    if not pdfs:
        print("未找到 PDF 文件")
        return
    print(f"找到 {len(pdfs)} 个 PDF 文件")
    articles = []
    for pdf in pdfs:
        art = import_pdf(os.path.join(dir_path, pdf))
        if art:
            articles.append(art)
    if articles:
        n = save_to_db(articles)
        print(f"✓ 成功导入 {n} 篇")
        export_json()
    else:
        print("未成功导入任何文件")

def cmd_export(args):
    out_dir = args.get("--out") or args.get("--dir")
    export_json(out_dir)

def main():
    import shlex
    args = sys.argv[1:] if len(sys.argv) > 1 else ["--help"]

    # Simple argv parser
    bool_flags = {"--download-pdf", "--help", "-h"}
    parsed = {"_extra": []}
    i = 0
    while i < len(args):
        if args[i] in ("--query", "--max", "--dir", "--out"):
            if i + 1 < len(args):
                parsed[args[i]] = args[i + 1]
                i += 2
            else:
                i += 1
        elif args[i] in bool_flags:
            parsed[args[i]] = True
            i += 1
        elif args[i].startswith("--"):
            i += 1
        else:
            parsed["_extra"].append(args[i])
            i += 1

    cmds = parsed["_extra"]

    if not cmds or "--help" in args or "-h" in args:
        print(__doc__)
        return

    cmd = cmds[0]
    if cmd == "stats":
        cmd_stats()
    elif cmd == "pubmed":
        cmd_pubmed(parsed)
    elif cmd == "pdf":
        cmd_pdf(parsed)
    elif cmd == "export":
        cmd_export(parsed)
    else:
        print(f"未知命令: {cmd}")
        print(__doc__)

if __name__ == "__main__":
    main()
