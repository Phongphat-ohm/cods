"""
JADS Storage Service - SQLite Persistence Engine (100% Offline & Air-Gapped)
Provides robust ACID compliance, WAL mode concurrency, atomic state persistence,
and automated migration from legacy JSON storage.
"""

import sys
import os
import json
import sqlite3
import uuid
import shutil
from typing import List, Dict, Any, Optional

from constants import PRESET_ROLES


def get_app_dir() -> str:
    """Get the root application directory (directory of the executable or project root)."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_bundle_dir() -> str:
    """Get the bundle directory for static resources (handles PyInstaller _MEIPASS)."""
    if getattr(sys, 'frozen', False):
        return getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def resolve_data_dir() -> str:
    """
    Resolve persistent data directory:
    - Portable / dev mode: uses 'data/' folder beside the executable or project root.
    - Read-only install fallback: uses '%LOCALAPPDATA%/JADS/data' if local directory is not writable.
    """
    app_dir = get_app_dir()
    local_data = os.path.join(app_dir, "data")
    try:
        os.makedirs(local_data, exist_ok=True)
        # Test write permission
        test_file = os.path.join(local_data, ".write_test")
        with open(test_file, "w") as f:
            f.write("ok")
        os.remove(test_file)
        return local_data
    except (PermissionError, OSError):
        appdata_dir = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "JADS", "data")
        os.makedirs(appdata_dir, exist_ok=True)
        return appdata_dir


def get_templates_dir() -> str:
    """
    Resolve directory for Word templates (.docx).
    Auto-populates bundled templates into local templates folder if missing.
    """
    local_tpl = os.path.join(get_app_dir(), "templates")
    if os.path.exists(local_tpl) and any(f.endswith(".docx") for f in os.listdir(local_tpl)):
        return local_tpl

    bundle_tpl = os.path.join(get_bundle_dir(), "templates")
    if os.path.exists(bundle_tpl) and any(f.endswith(".docx") for f in os.listdir(bundle_tpl)):
        try:
            os.makedirs(local_tpl, exist_ok=True)
            for f in os.listdir(bundle_tpl):
                src = os.path.join(bundle_tpl, f)
                dst = os.path.join(local_tpl, f)
                if os.path.isfile(src) and not os.path.exists(dst):
                    shutil.copy2(src, dst)
            return local_tpl
        except Exception:
            return bundle_tpl
    return local_tpl


def get_fonts_dir() -> str:
    """Resolve directory containing TrueType Kanit fonts."""
    local_fonts = os.path.join(get_app_dir(), "fonts")
    if os.path.exists(local_fonts) and any(f.lower().endswith((".ttf", ".otf")) for f in os.listdir(local_fonts)):
        return local_fonts

    bundle_fonts = os.path.join(get_bundle_dir(), "fonts")
    if os.path.exists(bundle_fonts):
        return bundle_fonts
    return local_fonts


def get_logo_path() -> str:
    """Resolve path to logo.png."""
    local_logo = os.path.join(get_app_dir(), "logo.png")
    if os.path.exists(local_logo):
        return local_logo

    bundle_logo = os.path.join(get_bundle_dir(), "logo.png")
    if os.path.exists(bundle_logo):
        return bundle_logo

    cwd_logo = os.path.join(os.getcwd(), "logo.png")
    if os.path.exists(cwd_logo):
        return cwd_logo
    return ""


# Base paths for application storage
DATA_DIR = resolve_data_dir()
DB_FILE = os.path.join(DATA_DIR, "jads.db")

# Legacy JSON file references for migration & backward compatibility
LEGACY_TEMPLATES_FILE = os.path.join(DATA_DIR, "paragraph_templates.json")
LEGACY_BENCH_PAIRS_FILE = os.path.join(DATA_DIR, "bench_pairs.json")
LEGACY_APP_CONFIG_FILE = os.path.join(DATA_DIR, "app_config.json")
TEMPLATES_FILE = LEGACY_TEMPLATES_FILE
BENCH_PAIRS_FILE = LEGACY_BENCH_PAIRS_FILE
APP_CONFIG_FILE = LEGACY_APP_CONFIG_FILE


def atomic_save_json(file_path: str, data: Any) -> bool:
    """Legacy helper maintained for backward compatibility."""
    ensure_data_dir()
    temp_path = f"{file_path}.tmp_{uuid.uuid4().hex[:6]}"
    try:
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp_path, file_path)
        return True
    except Exception:
        return False

# Standard court templates curated for Thai judicial proceedings
DEFAULT_TEMPLATES: List[Dict[str, Any]] = [
    {
        "id": "tpl_1",
        "title": "นัดพร้อมเพื่อกำหนดวันนัดสืบพยาน",
        "category": "นัดพร้อม / กำหนดวัน",
        "content": "นัดพร้อมวันนี้ ทนายโจทก์และทนายจำเลยมาศาล ศาลสอบคู่ความแล้ว แถลงว่าคดีนี้ตกลงกันไม่ได้ จึงประสงค์จะสืบพยานต่อไป คู่ความกำหนดวันนัดสืบพยานร่วมกัน โดยโจทก์นำสืบพยาน ๑ นัด จำเลยนำสืบพยาน ๑ นัด จึงให้นัดสืบพยานโจทก์ในวันที่ ... และนัดสืบพยานจำเลยในวันที่ ... ให้คู่ความเตรียมพยานมาให้พร้อมสืบในวันนัด"
    },
    {
        "id": "tpl_2",
        "title": "นัดฟังคำพิพากษา / คำสั่ง",
        "category": "คำพิพากษา",
        "content": "นัดฟังคำพิพากษาวันนี้ โจทก์และจำเลยมาศาล ศาลได้อ่านคำพิพากษาให้คู่ความฟังแล้ว คู่ความลงลายมือชื่อรับทราบ"
    },
    {
        "id": "tpl_3",
        "title": "ทำสัญญาประนีประนอมยอมความ",
        "category": "ไกล่เกลี่ย / ยอมความ",
        "content": "วันนี้ ทนายโจทก์และทนายจำเลยมาศาล คู่ความแถลงว่าสามารถตกลงระงับข้อพิพาทกันได้ จึงได้ทำสัญญาประนีประนอมยอมความฉบับลงวันที่วันนี้เสนอต่อศาล ศาลได้ตรวจสัญญาประนีประนอมยอมความแล้ว เห็นว่าไม่ขัดต่อกฎหมายและคู่ความได้ลงลายมือชื่อถูกต้อง จึงพิพากษาตามยอม คดีเป็นอันเสร็จเด็ดขาด"
    },
    {
        "id": "tpl_4",
        "title": "จำเลยให้การรับสารภาพ (คดีอาญา)",
        "category": "คดีอาญา",
        "content": "นัดพิจารณาวันนี้ พนักงานอัยการโจทก์ จำเลย และทนายจำเลยมาศาล ศาลได้อ่านและอธิบายฟ้องให้จำเลยฟัง จำเลยให้การรับสารภาพตามฟ้องทุกประการ ศาลเห็นว่าคดีมีพยานหลักฐานพอวินิจฉัยได้ จึงให้นัดฟังคำพิพากษาในวันที่ ... เวลา ๐๙.๐๐ นาฬิกา"
    },
    {
        "id": "tpl_5",
        "title": "คู่ความขอเลื่อนคดีเนื่องจากพยานป่วย",
        "category": "ขอเลื่อนคดี",
        "content": "นัดสืบพยานวันนี้ ทนายโจทก์และทนายจำเลยมาศาล ทนายโจทก์แถลงว่าพยานปากนาย ... มีอาการป่วยกะทันหันไม่สามารถเดินทางมาเบิกความได้ โดยมีใบรับรองแพทย์มาแสดง จึงขอเลื่อนการสืบพยานไปอีก ๑ นัด ทนายจำเลยไม่คัดค้าน ศาลเห็นว่ามีเหตุจำเป็นอันมิอาจก้าวล่วงได้ จึงอนุญาตให้เลื่อนไปนัดสืบพยานโจทก์ในวันที่ ..."
    },
    {
        "id": "tpl_6",
        "title": "โจทก์ขอถอนฟ้อง",
        "category": "ถอนฟ้อง / จำหน่ายคดี",
        "content": "วันนี้ โจทก์ยื่นคำร้องขอถอนฟ้อง แถลงว่าจำเลยได้ชำระหนี้ตามฟ้องครบถ้วนแล้ว จึงไม่ประสงค์จะดำเนินคดีต่อไป จำเลยแถลงไม่คัดค้าน ศาลพิจารณาแล้วอนุญาตให้โจทก์ถอนฟ้องได้ ให้จำหน่ายคดีออกจากสารบบความ คืนเงินค่าขึ้นศาลตามระเบียบ"
    },
    {
        "id": "tpl_7",
        "title": "นัดชี้สองสถานและกำหนดแนวทางนำสืบ",
        "category": "ชี้สองสถาน",
        "content": "นัดชี้สองสถานวันนี้ ทนายโจทก์และทนายจำเลยมาศาล ศาลได้ตรวจคำฟ้อง คำให้การ และสอบถามคู่ความแล้ว กำหนดประเด็นข้อพิพาทและหน้าที่นำสืบดังนี้ ๑. จำเลยผิดสัญญาตามฟ้องหรือไม่ (โจทก์มีหน้าที่นำสืบ) ๒. ค่าเสียหายมีเพียงใด (โจทก์มีหน้าที่นำสืบ) ให้นัดสืบพยานโจทก์ในวันที่ ... และนัดสืบพยานจำเลยในวันที่ ..."
    }
]

# Standard sample bench pairings
DEFAULT_BENCH_PAIRS: List[Dict[str, Any]] = [
    {"judge1": "นายธีรวัฒน์ จันทร์เพ็ญ", "judge2": "นางสาวศิริพร บุญเสริม", "note": "บัลลังก์ 4"},
    {"judge1": "นายสมชาย วิริยะการุณย์", "judge2": "นายเกียรติศักดิ์ ชัยชนะ", "note": "บัลลังก์ 7"},
    {"judge1": "นางสาวนันทนา สุขเกษม", "judge2": "นายประวิทย์ รัตนโชติ", "note": "บัลลังก์ 2"}
]

# Comprehensive Thai judicial titles for prefix-insensitive name matching
KNOWN_PREFIXES = [
    "ม.ร.ว.", "ม.ล.", "พ.ต.อ.", "พ.ต.ท.", "ร.ต.อ.", "พ.ต.ต.", "พ.ต.", "ร.ต.",
    "ผศ.ดร.", "รศ.ดร.", "ศ.ดร.", "ผศ.", "รศ.", "ศ.", "ดร.",
    "นางสาว", "น.ส.", "นาย", "นาง", "ท่าน"
]


def ensure_data_dir() -> str:
    """Ensure the local data directory exists and return its absolute path."""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR, exist_ok=True)
    return DATA_DIR


def get_db_connection() -> sqlite3.Connection:
    """Create and configure a robust SQLite database connection with WAL mode."""
    ensure_data_dir()
    conn = sqlite3.connect(DB_FILE, timeout=15.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA synchronous = NORMAL;")
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


_DB_INITIALIZED = False


def init_db(force: bool = False):
    """
    Initialize SQLite schema and automatically migrate data from existing JSON files.
    Ensures zero data loss while upgrading from legacy file storage.
    Migration runs exactly once per dataset and is tracked in 'schema_migrations',
    ensuring that if a user deletes all records, the table stays empty in the real database.
    """
    global _DB_INITIALIZED
    if _DB_INITIALIZED and not force:
        return

    ensure_data_dir()
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # 0. Migration tracking table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                name TEXT PRIMARY KEY,
                migrated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 1. App configuration table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS app_config (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 2. Paragraph templates table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS paragraph_templates (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                category TEXT DEFAULT 'ทั่วไป',
                content TEXT NOT NULL,
                sort_order INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_template_category ON paragraph_templates(category);")

        # 3. Bench pairs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bench_pairs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                judge1 TEXT NOT NULL UNIQUE,
                judge2 TEXT NOT NULL,
                note TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_bench_judge1 ON bench_pairs(judge1);")

        # 4. Signatory quick-add roles table (user-editable attendee chips)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS preset_roles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role TEXT NOT NULL UNIQUE,
                sort_order INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_preset_role_order ON preset_roles(sort_order);")

        conn.commit()

        # ================= Auto-Migration from Legacy JSON =================
        # Migration runs ONCE. Once recorded in schema_migrations,
        # it is NEVER re-executed, so if a user deletes all records, the table stays empty.

        # A. Migrate app_config
        cursor.execute("SELECT 1 FROM schema_migrations WHERE name = 'app_config_migrated'")
        if not cursor.fetchone():
            cursor.execute("SELECT COUNT(*) FROM app_config")
            existing_count = cursor.fetchone()[0]
            has_migrated_file = os.path.exists(f"{LEGACY_APP_CONFIG_FILE}.migrated")
            if existing_count == 0 and not has_migrated_file and os.path.exists(LEGACY_APP_CONFIG_FILE):
                try:
                    with open(LEGACY_APP_CONFIG_FILE, "r", encoding="utf-8") as f:
                        cfg = json.load(f)
                    if isinstance(cfg, dict):
                        for k, v in cfg.items():
                            cursor.execute("INSERT OR REPLACE INTO app_config (key, value) VALUES (?, ?)", (str(k), str(v)))
                        conn.commit()
                    bak_file = f"{LEGACY_APP_CONFIG_FILE}.migrated"
                    if not os.path.exists(bak_file):
                        shutil.copyfile(LEGACY_APP_CONFIG_FILE, bak_file)
                except Exception:
                    pass
            cursor.execute("INSERT OR REPLACE INTO schema_migrations (name) VALUES ('app_config_migrated')")
            conn.commit()

        # B. Migrate paragraph_templates
        cursor.execute("SELECT 1 FROM schema_migrations WHERE name = 'paragraph_templates_migrated'")
        if not cursor.fetchone():
            cursor.execute("SELECT COUNT(*) FROM paragraph_templates")
            existing_count = cursor.fetchone()[0]
            has_migrated_file = os.path.exists(f"{LEGACY_TEMPLATES_FILE}.migrated")
            if existing_count == 0 and not has_migrated_file:
                migrated_tpls = []
                if os.path.exists(LEGACY_TEMPLATES_FILE):
                    try:
                        with open(LEGACY_TEMPLATES_FILE, "r", encoding="utf-8") as f:
                            data = json.load(f)
                        if isinstance(data, list) and len(data) > 0:
                            migrated_tpls = data
                        bak_file = f"{LEGACY_TEMPLATES_FILE}.migrated"
                        if not os.path.exists(bak_file):
                            shutil.copyfile(LEGACY_TEMPLATES_FILE, bak_file)
                    except Exception:
                        pass

                target_tpls = migrated_tpls if migrated_tpls else DEFAULT_TEMPLATES
                for idx, t in enumerate(target_tpls):
                    t_id = t.get("id") or f"tpl_{idx+1}"
                    t_title = t.get("title", "")
                    t_cat = t.get("category", "ทั่วไป")
                    t_cnt = t.get("content", "")
                    cursor.execute("""
                        INSERT OR REPLACE INTO paragraph_templates (id, title, category, content, sort_order)
                        VALUES (?, ?, ?, ?, ?)
                    """, (t_id, t_title, t_cat, t_cnt, idx))
                conn.commit()
            cursor.execute("INSERT OR REPLACE INTO schema_migrations (name) VALUES ('paragraph_templates_migrated')")
            conn.commit()

        # C. Migrate bench_pairs
        cursor.execute("SELECT 1 FROM schema_migrations WHERE name = 'bench_pairs_migrated'")
        if not cursor.fetchone():
            cursor.execute("SELECT COUNT(*) FROM bench_pairs")
            existing_count = cursor.fetchone()[0]
            has_migrated_file = os.path.exists(f"{LEGACY_BENCH_PAIRS_FILE}.migrated")
            if existing_count == 0 and not has_migrated_file:
                migrated_pairs = []
                if os.path.exists(LEGACY_BENCH_PAIRS_FILE):
                    try:
                        with open(LEGACY_BENCH_PAIRS_FILE, "r", encoding="utf-8") as f:
                            data = json.load(f)
                        if isinstance(data, list) and len(data) > 0:
                            migrated_pairs = data
                        bak_file = f"{LEGACY_BENCH_PAIRS_FILE}.migrated"
                        if not os.path.exists(bak_file):
                            shutil.copyfile(LEGACY_BENCH_PAIRS_FILE, bak_file)
                    except Exception:
                        pass

                target_pairs = migrated_pairs if migrated_pairs else DEFAULT_BENCH_PAIRS
                for p in target_pairs:
                    j1 = p.get("judge1", "").strip()
                    j2 = p.get("judge2", "").strip()
                    note = p.get("note", "").strip()
                    if j1 and j2:
                        cursor.execute("""
                            INSERT OR IGNORE INTO bench_pairs (judge1, judge2, note)
                            VALUES (?, ?, ?)
                        """, (j1, j2, note))
                conn.commit()
            cursor.execute("INSERT OR REPLACE INTO schema_migrations (name) VALUES ('bench_pairs_migrated')")
            conn.commit()

        # D. Seed default signatory quick-add roles (runs once)
        cursor.execute("SELECT 1 FROM schema_migrations WHERE name = 'preset_roles_seeded'")
        if not cursor.fetchone():
            cursor.execute("SELECT COUNT(*) FROM preset_roles")
            if cursor.fetchone()[0] == 0:
                for idx, role in enumerate(PRESET_ROLES):
                    r = str(role).strip()
                    if r:
                        cursor.execute("""
                            INSERT OR IGNORE INTO preset_roles (role, sort_order)
                            VALUES (?, ?)
                        """, (r, idx))
                conn.commit()
            cursor.execute("INSERT OR REPLACE INTO schema_migrations (name) VALUES ('preset_roles_seeded')")
            conn.commit()

    _DB_INITIALIZED = True


# Automatically initialize schema on module import
init_db()


# ================= Paragraph Templates Management =================

def load_templates() -> List[Dict[str, Any]]:
    """Load paragraph templates from SQLite ordered by sort order."""
    init_db()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, title, category, content FROM paragraph_templates ORDER BY sort_order ASC, rowid ASC")
        rows = cursor.fetchall()
        return [{"id": r["id"], "title": r["title"], "category": r["category"], "content": r["content"]} for r in rows]


def save_templates(templates: List[Dict[str, Any]]) -> bool:
    """Save full paragraph templates list to SQLite atomically."""
    init_db()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM paragraph_templates")
        for idx, t in enumerate(templates):
            t_id = t.get("id") or f"tpl_{uuid.uuid4().hex[:8]}"
            cursor.execute("""
                INSERT INTO paragraph_templates (id, title, category, content, sort_order, updated_at)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (t_id, t.get("title", ""), t.get("category", "ทั่วไป"), t.get("content", ""), idx))
        conn.commit()
        return True


def add_template(title: str, content: str, category: str = "ทั่วไป") -> Dict[str, Any]:
    """Add a new custom paragraph template into SQLite."""
    init_db()
    new_id = f"tpl_user_{uuid.uuid4().hex[:8]}"
    item = {
        "id": new_id,
        "title": title.strip(),
        "category": category.strip() if category else "ทั่วไป",
        "content": content.strip()
    }
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COALESCE(MAX(sort_order), 0) + 1 FROM paragraph_templates")
        next_order = cursor.fetchone()[0]
        cursor.execute("""
            INSERT INTO paragraph_templates (id, title, category, content, sort_order)
            VALUES (?, ?, ?, ?, ?)
        """, (item["id"], item["title"], item["category"], item["content"], next_order))
        conn.commit()
    return item


def update_template(tpl_id: str, title: str, content: str, category: str = "ทั่วไป") -> bool:
    """Update an existing template by ID in SQLite."""
    init_db()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE paragraph_templates
            SET title = ?, content = ?, category = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (title.strip(), content.strip(), category.strip() if category else "ทั่วไป", tpl_id))
        conn.commit()
        return cursor.rowcount > 0


def delete_template(tpl_id: str) -> bool:
    """Delete a template by ID from SQLite."""
    init_db()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM paragraph_templates WHERE id = ?", (tpl_id,))
        conn.commit()
        return cursor.rowcount > 0


# ================= Bench Pairs Management =================

def normalize_judge_name(name: str) -> str:
    """
    Normalize judge name for matching by trimming whitespace and common prefixes
    without accidentally stripping parts of actual names.
    """
    clean = str(name).strip()
    for p in KNOWN_PREFIXES:
        if clean.startswith(p):
            clean = clean[len(p):].strip()
            break
    return clean


def is_name_match(name1: str, name2: str) -> bool:
    """Check if two judge names refer to the same person."""
    n1 = normalize_judge_name(name1)
    n2 = normalize_judge_name(name2)
    if not n1 or not n2:
        return False
    return n1 == n2 or n1 in n2 or n2 in n1


def load_bench_pairs() -> List[Dict[str, Any]]:
    """Load judge bench pairings from SQLite."""
    init_db()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, judge1, judge2, note FROM bench_pairs ORDER BY id ASC")
        rows = cursor.fetchall()
        return [
            {
                "id": r["id"],
                "judge1": r["judge1"],
                "judge2": r["judge2"],
                "note": r["note"] or ""
            }
            for r in rows
        ]


def save_bench_pairs(pairs: List[Dict[str, Any]]) -> bool:
    """Save bench pairings list to SQLite atomically."""
    init_db()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM bench_pairs")
        for p in pairs:
            j1 = p.get("judge1", "").strip()
            j2 = p.get("judge2", "").strip()
            note = p.get("note", "").strip()
            if j1 and j2:
                cursor.execute("""
                    INSERT OR REPLACE INTO bench_pairs (judge1, judge2, note, updated_at)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                """, (j1, j2, note))
        conn.commit()
        return True


def clear_all_bench_pairs() -> bool:
    """Delete all bench pairings from SQLite."""
    init_db()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM bench_pairs")
        conn.commit()
        return True


def find_paired_judge(judge1_name: str) -> Optional[str]:
    """Find the paired second judge for a given first judge name."""
    if not judge1_name or not str(judge1_name).strip():
        return None
    pairs = load_bench_pairs()
    for p in pairs:
        j1 = p.get("judge1", "")
        if is_name_match(j1, judge1_name):
            return p.get("judge2", "").strip() or None
    return None


def save_or_update_pair(judge1: str, judge2: str, note: Optional[str] = None, pair_id: Optional[int] = None) -> bool:
    """Add or update a bench pairing between two judges in SQLite."""
    j1 = str(judge1).strip()
    j2 = str(judge2).strip()
    if not j1 or not j2:
        return False

    init_db()
    note_val = note.strip() if note is not None else ""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        if pair_id is not None:
            cursor.execute("SELECT id FROM bench_pairs WHERE id = ?", (pair_id,))
            if cursor.fetchone():
                cursor.execute("""
                    UPDATE bench_pairs
                    SET judge1 = ?, judge2 = ?, note = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (j1, j2, note_val, pair_id))
                conn.commit()
                return True

        # Check existing by exact or fuzzy match
        cursor.execute("SELECT id, judge1 FROM bench_pairs")
        rows = cursor.fetchall()
        matched_id = None
        for r in rows:
            if is_name_match(r["judge1"], j1):
                matched_id = r["id"]
                break

        if matched_id is not None:
            cursor.execute("""
                UPDATE bench_pairs
                SET judge1 = ?, judge2 = ?, note = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (j1, j2, note_val, matched_id))
        else:
            cursor.execute("""
                INSERT OR REPLACE INTO bench_pairs (judge1, judge2, note, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            """, (j1, j2, note_val))
        conn.commit()
        return True


def delete_bench_pair(judge1: str = "", pair_id: Optional[int] = None) -> bool:
    """Delete a bench pairing by ID or judge 1 name from SQLite."""
    init_db()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        if pair_id is not None:
            cursor.execute("DELETE FROM bench_pairs WHERE id = ?", (pair_id,))
            conn.commit()
            if cursor.rowcount > 0:
                return True

        clean_j1 = str(judge1).strip() if judge1 else ""
        if clean_j1:
            # 1. Exact match on judge1
            cursor.execute("DELETE FROM bench_pairs WHERE judge1 = ?", (clean_j1,))
            conn.commit()
            if cursor.rowcount > 0:
                return True

            # 2. Fuzzy match on judge1
            cursor.execute("SELECT id, judge1 FROM bench_pairs")
            rows = cursor.fetchall()
            for r in rows:
                if is_name_match(r["judge1"], clean_j1):
                    cursor.execute("DELETE FROM bench_pairs WHERE id = ?", (r["id"],))
                    conn.commit()
                    return cursor.rowcount > 0

        return False


# ================= Signatory Quick-Add Roles (Preset Role Chips) =================
def load_preset_roles() -> List[Dict[str, Any]]:
    """Load user-editable signatory quick-add roles from SQLite ordered by sort order."""
    init_db()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, role FROM preset_roles ORDER BY sort_order ASC, rowid ASC")
        rows = cursor.fetchall()
        return [{"id": r["id"], "role": r["role"]} for r in rows]


def add_preset_role(role: str) -> bool:
    """Add a new quick-add role chip. Returns False if empty or already exists."""
    r = str(role).strip()
    if not r:
        return False
    init_db()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COALESCE(MAX(sort_order), -1) + 1 FROM preset_roles")
        next_order = cursor.fetchone()[0]
        cursor.execute("""
            INSERT OR IGNORE INTO preset_roles (role, sort_order)
            VALUES (?, ?)
        """, (r, next_order))
        conn.commit()
        return cursor.rowcount > 0


def update_preset_role(role_id: int, role: str) -> bool:
    """Update an existing quick-add role chip by ID."""
    r = str(role).strip()
    if not r:
        return False
    init_db()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE preset_roles
            SET role = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (r, role_id))
        conn.commit()
        return cursor.rowcount > 0


def delete_preset_role(role_id: int) -> bool:
    """Delete a quick-add role chip by ID."""
    init_db()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM preset_roles WHERE id = ?", (role_id,))
        conn.commit()
        return cursor.rowcount > 0


def clear_all_preset_roles() -> bool:
    """Delete all quick-add role chips."""
    init_db()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM preset_roles")
        conn.commit()
        return True


def reorder_preset_roles(ordered_ids: List[int]) -> bool:
    """Persist a new display order for quick-add role chips given a list of IDs."""
    init_db()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        for idx, r_id in enumerate(ordered_ids):
            cursor.execute("""
                UPDATE preset_roles
                SET sort_order = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (idx, r_id))
        conn.commit()
        return True


# ================= App Config / Court Settings =================

def load_app_config() -> Dict[str, Any]:
    """Load application configuration dictionary from SQLite."""
    init_db()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT key, value FROM app_config")
        rows = cursor.fetchall()
        return {r["key"]: r["value"] for r in rows}


def save_app_config(config: Dict[str, Any]) -> bool:
    """Save application configuration dictionary into SQLite."""
    if not isinstance(config, dict):
        return False
    init_db()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        for k, v in config.items():
            cursor.execute("""
                INSERT INTO app_config (key, value, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = CURRENT_TIMESTAMP
            """, (str(k), str(v)))
        conn.commit()
        return True


def get_default_court_name() -> str:
    """Get the saved default court name, or empty string if not configured."""
    init_db()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM app_config WHERE key = 'default_court_name'")
        row = cursor.fetchone()
        return str(row["value"]).strip() if row else ""


def set_default_court_name(court_name: str) -> bool:
    """Save the default court name to SQLite configuration."""
    c_name = str(court_name).strip()
    init_db()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO app_config (key, value, updated_at)
            VALUES ('default_court_name', ?, CURRENT_TIMESTAMP)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = CURRENT_TIMESTAMP
        """, (c_name,))
        conn.commit()
        return True
