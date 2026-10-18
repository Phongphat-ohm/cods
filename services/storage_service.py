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
import logging
from datetime import datetime
from contextlib import contextmanager
from typing import List, Dict, Any, Optional, Generator

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
        appdata_dir = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "CODS", "data")
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


def get_default_templates_dir() -> str:
    """Resolve directory containing factory default Word templates."""
    local_def = os.path.join(get_app_dir(), "default_templates")
    if os.path.exists(local_def) and any(f.endswith(".docx") for f in os.listdir(local_def)):
        return local_def

    bundle_def = os.path.join(get_bundle_dir(), "default_templates")
    if os.path.exists(bundle_def) and any(f.endswith(".docx") for f in os.listdir(bundle_def)):
        return bundle_def

    return local_def


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

# Migrate legacy jads.db to cods.db seamlessly if needed
_cods_db = os.path.join(DATA_DIR, "cods.db")
_jads_db = os.path.join(DATA_DIR, "jads.db")
if not os.path.exists(_cods_db) and os.path.exists(_jads_db):
    try:
        shutil.copy2(_jads_db, _cods_db)
    except Exception:
        pass
DB_FILE = _cods_db if (os.path.exists(_cods_db) or not os.path.exists(_jads_db)) else _jads_db

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

# No default seed templates - template storage starts clean/unseeded per user request
DEFAULT_TEMPLATES: List[Dict[str, Any]] = []

# No default seed bench pairs - bench pairing storage starts clean/unseeded per user request
DEFAULT_BENCH_PAIRS: List[Dict[str, Any]] = []


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


def check_and_recover_db():
    """
    Check SQLite database integrity. If corrupted, safely backup the corrupted
    files and allow creating a fresh, healthy database.
    """
    if not os.path.exists(DB_FILE):
        return

    is_corrupt = False
    try:
        conn = sqlite3.connect(DB_FILE, timeout=5.0)
        cursor = conn.cursor()
        cursor.execute("PRAGMA quick_check;")
        res = cursor.fetchone()
        if not res or res[0] != "ok":
            is_corrupt = True
        conn.close()
    except Exception as e:
        logging.error(f"Database integrity check failed: {e}")
        is_corrupt = True

    if is_corrupt:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        corrupt_backup = f"{DB_FILE}.corrupt_{timestamp}.bak"
        try:
            if os.path.exists(DB_FILE):
                os.rename(DB_FILE, corrupt_backup)
            for ext in ["-wal", "-shm"]:
                wal_f = f"{DB_FILE}{ext}"
                if os.path.exists(wal_f):
                    os.rename(wal_f, f"{corrupt_backup}{ext}")
            logging.error(f"Corrupted database backed up to {corrupt_backup}")
        except Exception as e:
            logging.error(f"Failed to isolate corrupted database: {e}")


def get_db_connection() -> sqlite3.Connection:
    """Create and configure a robust SQLite database connection with WAL mode."""
    ensure_data_dir()
    conn = sqlite3.connect(DB_FILE, timeout=30.0, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA synchronous = NORMAL;")
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA busy_timeout = 30000;")
    return conn


@contextmanager
def get_db() -> Generator[sqlite3.Connection, None, None]:
    """
    Safe context manager for database operations:
    - Auto commit on clean completion
    - Auto rollback on exceptions
    - Auto close connection in finally block (prevents connection & file descriptor leaks 100%)
    """
    conn = get_db_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


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

    check_and_recover_db()
    ensure_data_dir()
    with get_db() as conn:
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
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_template_sort ON paragraph_templates(sort_order ASC);")

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

        # 5. Recent court schedule files (MRU)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS recent_files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT NOT NULL UNIQUE,
                file_name TEXT NOT NULL,
                file_size INTEGER DEFAULT 0,
                case_count INTEGER DEFAULT 0,
                last_opened TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_recent_files_opened ON recent_files(last_opened DESC);")

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

                if migrated_tpls:
                    for idx, t in enumerate(migrated_tpls):
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

                target_pairs = migrated_pairs if migrated_pairs else []
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

        # One-time safe purge of default legacy sample data without affecting real user entries
        cursor.execute("SELECT 1 FROM schema_migrations WHERE name = 'legacy_seeds_purged'")
        if not cursor.fetchone():
            cursor.execute("DELETE FROM paragraph_templates WHERE id IN ('tpl_1', 'tpl_2', 'tpl_3', 'tpl_4', 'tpl_5', 'tpl_6', 'tpl_7')")
            cursor.execute("DELETE FROM bench_pairs WHERE judge1 IN ('นาย ชาญชัย ยุติธรรม', 'นาง วราภรณ์ สถิตธรรม', 'นายธีรวัฒน์ จันทร์เพ็ญ', 'นายสมชาย วิริยะการุณย์', 'นางสาวนันทนา สุขเกษม')")
            cursor.execute("INSERT OR REPLACE INTO schema_migrations (name) VALUES ('legacy_seeds_purged')")
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
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, title, category, content FROM paragraph_templates ORDER BY sort_order ASC, rowid ASC")
        rows = cursor.fetchall()
        return [{"id": r["id"], "title": r["title"], "category": r["category"], "content": r["content"]} for r in rows]


def save_templates(templates: List[Dict[str, Any]]) -> bool:
    """Save full paragraph templates list to SQLite atomically without data loss."""
    if not isinstance(templates, list):
        return False
    init_db()
    with get_db() as conn:
        cursor = conn.cursor()
        incoming_ids = []
        for idx, t in enumerate(templates):
            t_id = t.get("id") or f"tpl_{uuid.uuid4().hex[:8]}"
            title = str(t.get("title", "")).strip()
            category = str(t.get("category", "ทั่วไป")).strip() or "ทั่วไป"
            content = str(t.get("content", "")).strip()
            if not title:
                continue
            incoming_ids.append(t_id)
            cursor.execute("""
                INSERT INTO paragraph_templates (id, title, category, content, sort_order, updated_at)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(id) DO UPDATE SET
                    title = excluded.title,
                    category = excluded.category,
                    content = excluded.content,
                    sort_order = excluded.sort_order,
                    updated_at = CURRENT_TIMESTAMP
            """, (t_id, title, category, content, idx))

        if incoming_ids:
            placeholders = ",".join("?" * len(incoming_ids))
            cursor.execute(f"DELETE FROM paragraph_templates WHERE id NOT IN ({placeholders})", incoming_ids)
        elif len(templates) == 0:
            cursor.execute("DELETE FROM paragraph_templates")
        return True


def reorder_templates(ordered_ids: List[str]) -> bool:
    """Safely update sort order of templates by list of IDs without touching data."""
    init_db()
    with get_db() as conn:
        cursor = conn.cursor()
        for idx, t_id in enumerate(ordered_ids):
            cursor.execute("""
                UPDATE paragraph_templates
                SET sort_order = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (idx, str(t_id)))
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
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COALESCE(MAX(sort_order), 0) + 1 FROM paragraph_templates")
        next_order = cursor.fetchone()[0]
        cursor.execute("""
            INSERT INTO paragraph_templates (id, title, category, content, sort_order)
            VALUES (?, ?, ?, ?, ?)
        """, (item["id"], item["title"], item["category"], item["content"], next_order))
    return item


def update_template(tpl_id: str, title: str, content: str, category: str = "ทั่วไป") -> bool:
    """Update an existing template by ID in SQLite."""
    init_db()
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE paragraph_templates
            SET title = ?, content = ?, category = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (title.strip(), content.strip(), category.strip() if category else "ทั่วไป", tpl_id))
        return cursor.rowcount > 0


def delete_template(tpl_id: str) -> bool:
    """Delete a template by ID from SQLite."""
    init_db()
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM paragraph_templates WHERE id = ?", (tpl_id,))
        return cursor.rowcount > 0


# ================= Bench Pairs Management =================

def normalize_judge_name(name: str) -> str:
    """
    Normalize judge name for matching by trimming whitespace and common prefixes
    without accidentally stripping parts of actual names.
    """
    clean = " ".join(str(name).strip().split())
    for p in KNOWN_PREFIXES:
        if clean.startswith(p):
            clean = clean[len(p):].strip()
            break
    return " ".join(clean.split())


def is_name_match(name1: str, name2: str) -> bool:
    """
    Check if two judge names refer to the same person.
    Uses strict normalization, exact equality, token permutation,
    and safe word/token matching without false substring collisions on short names.
    """
    n1 = normalize_judge_name(name1)
    n2 = normalize_judge_name(name2)
    if not n1 or not n2:
        return False
    if n1 == n2:
        return True

    # Compare set of name tokens (e.g. "สมชาย ใจดี" vs "ใจดี สมชาย")
    t1 = set(n1.split())
    t2 = set(n2.split())
    if len(t1) >= 2 and t1 == t2:
        return True
    if t1 and t2 and (t1.issubset(t2) or t2.issubset(t1)) and min(len(t1), len(t2)) >= 2:
        return True

    # For single token or continuous names: only allow substring if length is substantial (>= 6 chars)
    if len(n1) >= 6 and len(n2) >= 6:
        if n1 in n2 or n2 in n1:
            return True

    return False


def load_bench_pairs() -> List[Dict[str, Any]]:
    """Load judge bench pairings from SQLite."""
    init_db()
    with get_db() as conn:
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
    with get_db() as conn:
        cursor = conn.cursor()
        incoming_j1s = []
        for p in pairs:
            j1 = str(p.get("judge1", "")).strip()
            j2 = str(p.get("judge2", "")).strip()
            note = str(p.get("note", "")).strip()
            if j1 and j2:
                incoming_j1s.append(j1)
                cursor.execute("""
                    INSERT INTO bench_pairs (judge1, judge2, note, updated_at)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT(judge1) DO UPDATE SET
                        judge2 = excluded.judge2,
                        note = excluded.note,
                        updated_at = CURRENT_TIMESTAMP
                """, (j1, j2, note))
        if incoming_j1s:
            placeholders = ",".join("?" * len(incoming_j1s))
            cursor.execute(f"DELETE FROM bench_pairs WHERE judge1 NOT IN ({placeholders})", incoming_j1s)
        elif len(pairs) == 0:
            cursor.execute("DELETE FROM bench_pairs")
        return True


def clear_all_bench_pairs() -> bool:
    """Delete all bench pairings from SQLite."""
    init_db()
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM bench_pairs")
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
    if not j1 or not j2 or j1 == j2:
        return False

    init_db()
    note_val = note.strip() if note is not None else ""
    with get_db() as conn:
        cursor = conn.cursor()
        if pair_id is not None:
            cursor.execute("SELECT id FROM bench_pairs WHERE id = ?", (pair_id,))
            if cursor.fetchone():
                cursor.execute("""
                    UPDATE bench_pairs
                    SET judge1 = ?, judge2 = ?, note = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (j1, j2, note_val, pair_id))
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
                INSERT INTO bench_pairs (judge1, judge2, note, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(judge1) DO UPDATE SET
                    judge2 = excluded.judge2,
                    note = excluded.note,
                    updated_at = CURRENT_TIMESTAMP
            """, (j1, j2, note_val))
        return True


def delete_bench_pair(judge1: str = "", pair_id: Optional[int] = None) -> bool:
    """Delete a bench pairing by ID or judge 1 name from SQLite."""
    init_db()
    with get_db() as conn:
        cursor = conn.cursor()
        if pair_id is not None:
            cursor.execute("DELETE FROM bench_pairs WHERE id = ?", (pair_id,))
            if cursor.rowcount > 0:
                return True

        clean_j1 = str(judge1).strip() if judge1 else ""
        if clean_j1:
            # 1. Exact match on judge1
            cursor.execute("DELETE FROM bench_pairs WHERE judge1 = ?", (clean_j1,))
            if cursor.rowcount > 0:
                return True

            # 2. Fuzzy match on judge1
            cursor.execute("SELECT id, judge1 FROM bench_pairs")
            rows = cursor.fetchall()
            for r in rows:
                if is_name_match(r["judge1"], clean_j1):
                    cursor.execute("DELETE FROM bench_pairs WHERE id = ?", (r["id"],))
                    return cursor.rowcount > 0

        return False


# ================= Signatory Quick-Add Roles (Preset Role Chips) =================
def load_preset_roles() -> List[Dict[str, Any]]:
    """Load user-editable signatory quick-add roles from SQLite ordered by sort order."""
    init_db()
    with get_db() as conn:
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
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COALESCE(MAX(sort_order), -1) + 1 FROM preset_roles")
        next_order = cursor.fetchone()[0]
        cursor.execute("""
            INSERT OR IGNORE INTO preset_roles (role, sort_order)
            VALUES (?, ?)
        """, (r, next_order))
        return cursor.rowcount > 0


def update_preset_role(role_id: int, role: str) -> bool:
    """Update an existing quick-add role chip by ID."""
    r = str(role).strip()
    if not r:
        return False
    init_db()
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE preset_roles
            SET role = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (r, role_id))
        return cursor.rowcount > 0


def delete_preset_role(role_id: int) -> bool:
    """Delete a quick-add role chip by ID."""
    init_db()
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM preset_roles WHERE id = ?", (role_id,))
        return cursor.rowcount > 0


def clear_all_preset_roles() -> bool:
    """Delete all quick-add role chips."""
    init_db()
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM preset_roles")
        return True


def reorder_preset_roles(ordered_ids: List[int]) -> bool:
    """Persist a new display order for quick-add role chips given a list of IDs."""
    init_db()
    with get_db() as conn:
        cursor = conn.cursor()
        for idx, r_id in enumerate(ordered_ids):
            cursor.execute("""
                UPDATE preset_roles
                SET sort_order = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (idx, r_id))
        return True


# ================= App Config / Court Settings =================

def load_app_config() -> Dict[str, Any]:
    """Load application configuration dictionary from SQLite."""
    init_db()
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT key, value FROM app_config")
        rows = cursor.fetchall()
        return {r["key"]: r["value"] for r in rows}


def save_app_config(config: Dict[str, Any]) -> bool:
    """Save application configuration dictionary into SQLite."""
    if not isinstance(config, dict):
        return False
    init_db()
    with get_db() as conn:
        cursor = conn.cursor()
        for k, v in config.items():
            cursor.execute("""
                INSERT INTO app_config (key, value, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = CURRENT_TIMESTAMP
            """, (str(k), str(v)))
        return True


def get_default_court_name() -> str:
    """Get the saved default court name, or empty string if not configured."""
    init_db()
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM app_config WHERE key = 'default_court_name'")
        row = cursor.fetchone()
        return str(row["value"]).strip() if row else ""


def set_default_court_name(court_name: str) -> bool:
    """Save the default court name to SQLite configuration."""
    c_name = str(court_name).strip()
    init_db()
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO app_config (key, value, updated_at)
            VALUES ('default_court_name', ?, CURRENT_TIMESTAMP)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = CURRENT_TIMESTAMP
        """, (c_name,))
        return True


def get_default_online_platform() -> str:
    """Get the saved default online meeting platform (defaults to 'Google Meet')."""
    init_db()
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM app_config WHERE key = 'default_online_platform'")
        row = cursor.fetchone()
        val = str(row["value"]).strip() if row and row["value"] else ""
        return val if val else "Google Meet"


def set_default_online_platform(platform_name: str) -> bool:
    """Save the default online meeting platform to SQLite configuration."""
    p_name = str(platform_name).strip() or "Google Meet"
    init_db()
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO app_config (key, value, updated_at)
            VALUES ('default_online_platform', ?, CURRENT_TIMESTAMP)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = CURRENT_TIMESTAMP
        """, (p_name,))
        return True


def get_online_platforms() -> List[str]:
    """Return list of standard online platforms with default platform prioritized."""
    from constants import DEFAULT_ONLINE_PLATFORMS
    default_p = get_default_online_platform()
    res = [default_p]
    for p in DEFAULT_ONLINE_PLATFORMS:
        if p.lower() != default_p.lower():
            res.append(p)
    return res


# ================= Tutorial & Onboarding State =================


def is_tutorial_completed(tutorial_key: str) -> bool:
    """
    Check if a specific tutorial or onboarding step has been completed or dismissed.
    Key examples: 'welcome_wizard', 'step_import', 'step_table', 'step_doctype', 'step_form'
    """
    init_db()
    db_key = f"tut_{tutorial_key}"
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM app_config WHERE key = ?", (db_key,))
        row = cursor.fetchone()
        if not row:
            return False
        return str(row["value"]).strip().lower() in ("1", "true", "yes", "completed")


def mark_tutorial_completed(tutorial_key: str, completed: bool = True) -> bool:
    """
    Mark a specific tutorial as completed or uncompleted in SQLite app_config.
    """
    init_db()
    db_key = f"tut_{tutorial_key}"
    val = "true" if completed else "false"
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO app_config (key, value, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = CURRENT_TIMESTAMP
        """, (db_key, val))
        return True


def reset_all_tutorials() -> bool:
    """
    Reset all tutorial states so the user can experience the guides and tours again.
    """
    init_db()
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM app_config WHERE key LIKE 'tut_%'")
        return True


# ================= Recent Files Management =================

def add_recent_file(file_path: str, file_name: str, file_size: int = 0, case_count: int = 0) -> bool:
    """Add or update a recently opened court schedule file (keeps top 15)."""
    if not file_path:
        return False
    init_db()
    norm_path = os.path.abspath(file_path)
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO recent_files (file_path, file_name, file_size, case_count, last_opened)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(file_path) DO UPDATE SET
                file_name = excluded.file_name,
                file_size = excluded.file_size,
                case_count = excluded.case_count,
                last_opened = CURRENT_TIMESTAMP
        """, (norm_path, file_name, file_size, case_count))

        # Keep only the 15 most recently opened files
        cursor.execute("""
            DELETE FROM recent_files
            WHERE id NOT IN (
                SELECT id FROM recent_files ORDER BY last_opened DESC LIMIT 15
            )
        """)
        return True


def get_recent_files() -> List[Dict[str, Any]]:
    """Retrieve list of recently opened files that still exist on disk."""
    init_db()
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, file_path, file_name, file_size, case_count, last_opened
            FROM recent_files
            ORDER BY last_opened DESC
        """)
        rows = cursor.fetchall()
        valid = []
        for r in rows:
            p = r["file_path"]
            if os.path.exists(p):
                valid.append({
                    "id": r["id"],
                    "file_path": p,
                    "file_name": r["file_name"],
                    "file_size": r["file_size"],
                    "case_count": r["case_count"],
                    "last_opened": r["last_opened"]
                })
        return valid


def clear_recent_files() -> bool:
    """Clear all recent files history."""
    init_db()
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM recent_files")
        return True

