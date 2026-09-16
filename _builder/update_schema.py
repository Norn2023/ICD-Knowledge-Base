#!/usr/bin/env python3
"""
更新现有数据库，添加文献库等相关表（不破坏已有数据）
"""
import sqlite3, os, sys
if sys.platform == "win32" and sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DB_PATH = os.path.join(os.path.dirname(__file__), "icd_kb.db")

LITERATURE_SQL = """
CREATE TABLE IF NOT EXISTS literature (
    id          INTEGER PRIMARY KEY,
    pmid        TEXT UNIQUE,
    title       TEXT NOT NULL,
    title_cn    TEXT,
    authors     TEXT,
    journal     TEXT,
    year        INTEGER,
    doi         TEXT,
    abstract    TEXT,
    full_text   TEXT,
    keywords    TEXT,
    lang        TEXT DEFAULT 'en',
    source      TEXT DEFAULT 'PubMed',
    url         TEXT,
    pdf_path    TEXT,
    notes       TEXT,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_literature_year ON literature(year);
CREATE INDEX IF NOT EXISTS idx_literature_journal ON literature(journal);
CREATE INDEX IF NOT EXISTS idx_literature_lang ON literature(lang);

CREATE VIRTUAL TABLE IF NOT EXISTS literature_fts USING fts5(
    title, title_cn, abstract, full_text, keywords,
    content='literature',
    content_rowid='id',
    tokenize='unicode61 remove_diacritics 2'
);

CREATE TABLE IF NOT EXISTS qa_log (
    id          INTEGER PRIMARY KEY,
    query       TEXT NOT NULL,
    answer      TEXT NOT NULL,
    sources     TEXT,
    model       TEXT DEFAULT 'local',
    tokens_in   INTEGER,
    tokens_out  INTEGER,
    time_ms     INTEGER,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
);
"""

def update():
    if not os.path.exists(DB_PATH):
        print(f"数据库不存在: {DB_PATH}")
        print("请先运行 python init_db.py 初始化数据库")
        return False

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(LITERATURE_SQL)
    conn.commit()
    # 重建 FTS 索引（确保已有数据的全文索引生效）
    try:
        conn.execute("INSERT INTO literature_fts(literature_fts) VALUES('rebuild')")
        conn.commit()
        count = conn.execute("SELECT COUNT(*) FROM literature_fts").fetchone()[0]
        print(f"[OK] 文献库表已添加, FTS 索引 {count} 条")
    except Exception as e:
        print(f"[OK] 文献库表已添加 (FTS跳过: {e})")
    conn.close()
    return True

if __name__ == "__main__":
    update()
