"""重建 FTS5 全文搜索索引"""
import sqlite3, os

DB_PATH = os.path.join(os.path.dirname(__file__), "icd_kb.db")
conn = sqlite3.connect(DB_PATH)

# 重建 FTS 索引（从源表重新填充）
conn.executescript("""
    INSERT INTO literature_fts(literature_fts) VALUES('rebuild');
""")
conn.commit()

count = conn.execute("SELECT COUNT(*) FROM literature_fts").fetchone()[0]
print(f"FTS 索引重建完成: {count} 条")
conn.close()
