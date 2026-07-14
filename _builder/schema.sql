-- ============================================================
-- ICD 编码知识库 · 数据库骨架
-- 表：icd10 / icd9 / drg / dip / cases
-- ============================================================

-- ── ICD-10 疾病诊断 ──────────────────────────────────────

CREATE TABLE icd10_chapters (
    id          INTEGER PRIMARY KEY,
    chapter_no  INTEGER NOT NULL,        -- 章号 1-22
    code_range  TEXT    NOT NULL,        -- 编码范围 e.g. "A00-B99"
    name        TEXT    NOT NULL,        -- 章名称
    folder_name TEXT    NOT NULL,        -- 对应 Obsidian 文件夹名
    notes       TEXT                     -- 编码要点
);

CREATE TABLE icd10_sections (
    id          INTEGER PRIMARY KEY,
    chapter_id  INTEGER NOT NULL REFERENCES icd10_chapters(id),
    code_range  TEXT    NOT NULL,        -- 节编码范围 e.g. "A00-A09"
    name        TEXT    NOT NULL,        -- 节名称
    includes    TEXT,                    -- 包括
    excludes    TEXT,                    -- 不包括
    rules       TEXT,                    -- 编码规则
    FOREIGN KEY (chapter_id) REFERENCES icd10_chapters(id)
);

CREATE TABLE icd10_codes (
    id          INTEGER PRIMARY KEY,
    section_id  INTEGER NOT NULL REFERENCES icd10_sections(id),
    code        TEXT    NOT NULL,        -- 完整编码 e.g. "A00.0"
    name        TEXT    NOT NULL,        -- 名称
    is_primary  INTEGER DEFAULT 1,       -- 是否主要编码
    star_code   TEXT,                    -- 星号对应编码
    sword_code  TEXT,                    -- 剑号对应编码
    notes       TEXT,                    -- 备注
    FOREIGN KEY (section_id) REFERENCES icd10_sections(id)
);

CREATE UNIQUE INDEX idx_icd10_code ON icd10_codes(code);

-- ── ICD-9 手术操作 ──────────────────────────────────────

CREATE TABLE icd9_chapters (
    id          INTEGER PRIMARY KEY,
    chapter_no  INTEGER NOT NULL,
    code_range  TEXT    NOT NULL,
    name        TEXT    NOT NULL,
    folder_name TEXT    NOT NULL,
    notes       TEXT
);

CREATE TABLE icd9_codes (
    id          INTEGER PRIMARY KEY,
    chapter_id  INTEGER NOT NULL REFERENCES icd9_chapters(id),
    code        TEXT    NOT NULL,        -- e.g. "47.09"
    name        TEXT    NOT NULL,
    category    TEXT,                    -- 类目 e.g. "47"
    notes       TEXT,
    FOREIGN KEY (chapter_id) REFERENCES icd9_chapters(id)
);

CREATE UNIQUE INDEX idx_icd9_code ON icd9_codes(code);

-- ── DRG 2.0 分组 ────────────────────────────────────────

CREATE TABLE drg_mdc (
    id          INTEGER PRIMARY KEY,
    mdc_code    TEXT    NOT NULL UNIQUE,   -- e.g. "MDCF"
    name        TEXT    NOT NULL,
    icd10_range TEXT                      -- 相关 ICD-10 范围
);

CREATE TABLE drg_adrg (
    id          INTEGER PRIMARY KEY,
    mdc_id      INTEGER NOT NULL REFERENCES drg_mdc(id),
    adrg_code   TEXT    NOT NULL UNIQUE,   -- e.g. "FM3"
    name        TEXT    NOT NULL,
    type        TEXT    NOT NULL CHECK(type IN ('surgical','medical','other')),
    FOREIGN KEY (mdc_id) REFERENCES drg_mdc(id)
);

CREATE TABLE drg_groups (
    id          INTEGER PRIMARY KEY,
    adrg_id     INTEGER NOT NULL REFERENCES drg_adrg(id),
    drg_code    TEXT    NOT NULL UNIQUE,   -- e.g. "FM31"
    name        TEXT    NOT NULL,
    severity    TEXT    NOT NULL CHECK(severity IN ('MCC','CC','noCC','unspecified')),
    weight      REAL,                      -- RW 值
    avg_cost    REAL,
    avg_days    REAL,
    FOREIGN KEY (adrg_id) REFERENCES drg_adrg(id)
);

-- DRG 与 ICD 编码的对应关系（多对多）
CREATE TABLE drg_diagnosis_map (
    id          INTEGER PRIMARY KEY,
    drg_id      INTEGER NOT NULL REFERENCES drg_groups(id),
    icd10_id    INTEGER NOT NULL REFERENCES icd10_codes(id),
    is_primary  INTEGER DEFAULT 1,        -- 1=主要诊断 0=其他诊断
    FOREIGN KEY (drg_id) REFERENCES drg_groups(id),
    FOREIGN KEY (icd10_id) REFERENCES icd10_codes(id)
);

CREATE TABLE drg_procedure_map (
    id          INTEGER PRIMARY KEY,
    drg_id      INTEGER NOT NULL REFERENCES drg_groups(id),
    icd9_id     INTEGER NOT NULL REFERENCES icd9_codes(id),
    is_primary  INTEGER DEFAULT 1,
    FOREIGN KEY (drg_id) REFERENCES drg_groups(id),
    FOREIGN KEY (icd9_id) REFERENCES icd9_codes(id)
);

-- ── DIP 3.0 病种分组 ────────────────────────────────────

CREATE TABLE dip_groups (
    id          INTEGER PRIMARY KEY,
    dip_code    TEXT    NOT NULL UNIQUE,   -- DIP 病种编码
    name        TEXT    NOT NULL,
    icd10_primary_id INTEGER REFERENCES icd10_codes(id),  -- 主要诊断
    icd9_primary_id  INTEGER REFERENCES icd9_codes(id),   -- 主要手术（可为空）
    avg_cost    REAL,
    weight      REAL,
    FOREIGN KEY (icd10_primary_id) REFERENCES icd10_codes(id),
    FOREIGN KEY (icd9_primary_id) REFERENCES icd9_codes(id)
);

-- ── 案例库 ──────────────────────────────────────────────

CREATE TABLE cases (
    id          INTEGER PRIMARY KEY,
    case_no     TEXT    NOT NULL UNIQUE,   -- 病案号
    gender      TEXT    CHECK(gender IN ('M','F','U')),
    age         INTEGER,
    admission   TEXT,                      -- 入院日期 YYYY-MM-DD
    discharge   TEXT,                      -- 出院日期
    dept        TEXT,                      -- 科室
    total_cost  REAL,                      -- 总费用
    drg_result  TEXT,                      -- 实际入组 DRG 编码
    dip_result  TEXT,                      -- 实际入组 DIP 编码
    notes       TEXT
);

CREATE TABLE case_diagnoses (
    id          INTEGER PRIMARY KEY,
    case_id     INTEGER NOT NULL REFERENCES cases(id),
    icd10_id    INTEGER NOT NULL REFERENCES icd10_codes(id),
    rank        INTEGER DEFAULT 1,         -- 1=主要诊断 2,3,4...=其他诊断
    FOREIGN KEY (case_id) REFERENCES cases(id),
    FOREIGN KEY (icd10_id) REFERENCES icd10_codes(id)
);

CREATE TABLE case_procedures (
    id          INTEGER PRIMARY KEY,
    case_id     INTEGER NOT NULL REFERENCES cases(id),
    icd9_id     INTEGER NOT NULL REFERENCES icd9_codes(id),
    rank        INTEGER DEFAULT 1,         -- 1=主要手术
    FOREIGN KEY (case_id) REFERENCES cases(id),
    FOREIGN KEY (icd9_id) REFERENCES icd9_codes(id)
);
