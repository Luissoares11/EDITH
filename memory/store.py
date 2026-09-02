import sqlite3
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from contextlib import contextmanager

from config import DB_PATH

@contextmanager
def db_session():
    """Context manager for safe, transaction-bound SQLite connections."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")  # Better concurrency/speed
    try:
        with conn:  # This automatically commits if no exception, or rolls back if one occurs
            yield conn
    finally:
        conn.close()

def init_db():
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    with db_session() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS facts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject TEXT NOT NULL,
                relation TEXT NOT NULL,
                object TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS collections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                owner TEXT NOT NULL,
                name TEXT NOT NULL,
                items TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(owner, name)
            );
            CREATE TABLE IF NOT EXISTS aliases (
                alias TEXT PRIMARY KEY,
                target TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                title TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER REFERENCES conversations(id),
                session_id TEXT NOT NULL,
                role TEXT CHECK(role IN ('user', 'assistant', 'system')),
                content TEXT NOT NULL,
                intent TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS corrections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id INTEGER REFERENCES messages(id),
                intent TEXT NOT NULL,
                field TEXT NOT NULL,
                edith_value TEXT,
                corrected_value TEXT NOT NULL,
                context TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS preferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                key TEXT NOT NULL,
                value TEXT NOT NULL,
                learned_from TEXT CHECK(learned_from IN ('explicit', 'inferred')),
                confidence REAL DEFAULT 1.0,
                confirmed BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(category, key)
            );
        """)

# ── Facts ───────────────────────────────────────────────────────
def add_fact(subject: str, relation: str, object_: str):
    with db_session() as conn:
        conn.execute(
            "INSERT INTO facts (subject, relation, object) VALUES (?, ?, ?)",
            (subject.lower(), relation.lower(), object_)
        )

def find_facts(subject: str = None, relation: str = None) -> List[Dict[str, Any]]:
    query = "SELECT subject, relation, object FROM facts WHERE 1=1"
    params = []
    if subject:
        query += " AND subject = ?"
        params.append(subject.lower())
    if relation:
        query += " AND relation = ?"
        params.append(relation.lower())
    
    with db_session() as conn:
        rows = conn.execute(query, params).fetchall()
        return [dict(row) for row in rows]

def replace_fact(subject: str, relation: str, object_: str):
    delete_facts(subject, relation)
    add_fact(subject, relation, object_)

def delete_facts(subject: str, relation: str = None) -> bool:
    query = "DELETE FROM facts WHERE subject = ?"
    params = [subject.lower()]
    if relation:
        query += " AND relation = ?"
        params.append(relation.lower())
    
    with db_session() as conn:
        cursor = conn.execute(query, params)
        return cursor.rowcount > 0

def dump_subject(subject: str) -> List[Dict[str, Any]]:
    return find_facts(subject=subject)

def list_entities() -> List[str]:
    with db_session() as conn:
        rows = conn.execute(
            "SELECT DISTINCT subject FROM facts WHERE subject != 'user'"
        ).fetchall()
        return [row["subject"] for row in rows]

# ── Collections ──────────────────────────────────────────────────
def set_collection(owner: str, name: str, items: List[str]):
    items_json = json.dumps(items)
    with db_session() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO collections (owner, name, items) VALUES (?, ?, ?)",
            (owner.lower(), name.lower(), items_json)
        )

def get_collection(owner: str, name: str) -> Optional[Dict[str, Any]]:
    with db_session() as conn:
        row = conn.execute(
            "SELECT owner, name, items FROM collections WHERE owner = ? AND name = ?",
            (owner.lower(), name.lower())
        ).fetchone()
        if row:
            res = dict(row)
            res["items"] = json.loads(res["items"])
            return res
        return None

def list_collections(owner: str) -> List[Dict[str, Any]]:
    with db_session() as conn:
        rows = conn.execute(
            "SELECT owner, name, items FROM collections WHERE owner = ?",
            (owner.lower(),)
        ).fetchall()
        result = []
        for row in rows:
            item = dict(row)
            item["items"] = json.loads(item["items"])
            result.append(item)
        return result

def add_collection_item(owner: str, name: str, item: str):
    col = get_collection(owner, name)
    if col:
        items = col["items"]
        items.append(item)
        set_collection(owner, name, items)
    else:
        set_collection(owner, name, [item])

def remove_collection_item(owner: str, name: str, index: int) -> Optional[str]:
    col = get_collection(owner, name)
    if not col or index < 0 or index >= len(col["items"]):
        return None
    removed = col["items"].pop(index)
    set_collection(owner, name, col["items"])
    return removed

def replace_collection_item(owner: str, name: str, old: str, new: str) -> bool:
    col = get_collection(owner, name)
    if not col or old not in col["items"]:
        return False
    idx = col["items"].index(old)
    col["items"][idx] = new
    set_collection(owner, name, col["items"])
    return True

def delete_collection(owner: str, name: str) -> bool:
    with db_session() as conn:
        cursor = conn.execute(
            "DELETE FROM collections WHERE owner = ? AND name = ?",
            (owner.lower(), name.lower())
        )
        return cursor.rowcount > 0

# ── Aliases ──────────────────────────────────────────────────────
def add_alias(alias: str, target: str):
    with db_session() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO aliases (alias, target) VALUES (?, ?)",
            (alias.lower(), target.lower())
        )

def get_aliases() -> Dict[str, str]:
    with db_session() as conn:
        rows = conn.execute("SELECT alias, target FROM aliases").fetchall()
        return {row["alias"]: row["target"] for row in rows}

# ── Conversations & Messages ──────────────────────────────────
def create_conversation(session_id: str, title: Optional[str] = None) -> int:
    """Create a new conversation session."""
    with db_session() as conn:
        cursor = conn.execute(
            "INSERT INTO conversations (session_id, title) VALUES (?, ?)",
            (session_id, title)
        )
        return cursor.lastrowid

def add_message(conversation_id: int, session_id: str, role: str, content: str, intent: Optional[str] = None) -> int:
    """Log a message in a conversation."""
    with db_session() as conn:
        cursor = conn.execute(
            "INSERT INTO messages (conversation_id, session_id, role, content, intent) VALUES (?, ?, ?, ?, ?)",
            (conversation_id, session_id, role, content, intent)
        )
        return cursor.lastrowid

def get_conversation_history(session_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    """Get the recent message history for a session."""
    with db_session() as conn:
        rows = conn.execute(
            """SELECT m.id, m.role, m.content, m.intent, m.created_at
               FROM messages m
               WHERE m.session_id = ?
               ORDER BY m.created_at DESC
               LIMIT ?""",
            (session_id, limit)
        ).fetchall()
        return [dict(row) for row in reversed(rows)]  # Reverse to get chronological order

# ── Corrections (Learning) ────────────────────────────────────
def log_correction(message_id: int, intent: str, field: str, corrected_value: str,
                   edith_value: Optional[str] = None, context: Optional[str] = None) -> int:
    """Log a correction when EDITH gets something wrong and the user fixes it."""
    with db_session() as conn:
        cursor = conn.execute(
            """INSERT INTO corrections
               (message_id, intent, field, edith_value, corrected_value, context)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (message_id, intent, field, edith_value, corrected_value, context)
        )
        return cursor.lastrowid

def get_corrections(intent: Optional[str] = None, field: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
    """Query the correction log."""
    query = "SELECT * FROM corrections WHERE 1=1"
    params = []
    if intent:
        query += " AND intent = ?"
        params.append(intent)
    if field:
        query += " AND field = ?"
        params.append(field)
    query += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)

    with db_session() as conn:
        rows = conn.execute(query, params).fetchall()
        return [dict(row) for row in rows]

def get_correction_patterns(intent: str) -> Dict[str, Any]:
    """Analyze corrections for a given intent to find patterns."""
    corrections = get_corrections(intent=intent)

    if not corrections:
        return {"intent": intent, "patterns": []}

    # Group by field
    field_corrections = {}
    for corr in corrections:
        field = corr["field"]
        if field not in field_corrections:
            field_corrections[field] = {"edith": {}, "corrected": {}}

        if corr["edith_value"]:
            edith_val = corr["edith_value"]
            field_corrections[field]["edith"][edith_val] = field_corrections[field]["edith"].get(edith_val, 0) + 1

        corr_val = corr["corrected_value"]
        field_corrections[field]["corrected"][corr_val] = field_corrections[field]["corrected"].get(corr_val, 0) + 1

    # Find patterns
    patterns = []
    for field, data in field_corrections.items():
        most_common_correction = max(data["corrected"].items(), key=lambda x: x[1])
        patterns.append({
            "field": field,
            "most_corrected_to": most_common_correction[0],
            "frequency": most_common_correction[1],
            "total_corrections": len(corrections)
        })

    return {
        "intent": intent,
        "total_corrections": len(corrections),
        "patterns": patterns
    }

# ── Preferences ───────────────────────────────────────────────
def set_preference(category: str, key: str, value: str, learned_from: str = "explicit", confidence: float = 1.0) -> int:
    """Store or update a preference."""
    with db_session() as conn:
        cursor = conn.execute(
            """INSERT OR REPLACE INTO preferences
               (category, key, value, learned_from, confidence)
               VALUES (?, ?, ?, ?, ?)""",
            (category, key, value, learned_from, confidence)
        )
        return cursor.lastrowid

def get_preference(category: str, key: str) -> Optional[Dict[str, Any]]:
    """Retrieve a specific preference."""
    with db_session() as conn:
        row = conn.execute(
            "SELECT * FROM preferences WHERE category = ? AND key = ?",
            (category, key)
        ).fetchone()
        return dict(row) if row else None

def get_preferences(category: Optional[str] = None) -> List[Dict[str, Any]]:
    """Get all preferences, optionally filtered by category."""
    query = "SELECT * FROM preferences WHERE 1=1"
    params = []
    if category:
        query += " AND category = ?"
        params.append(category)
    query += " ORDER BY category, key"

    with db_session() as conn:
        rows = conn.execute(query, params).fetchall()
        return [dict(row) for row in rows]

def confirm_preference(category: str, key: str) -> bool:
    """Mark a preference as confirmed (user validated it)."""
    with db_session() as conn:
        cursor = conn.execute(
            "UPDATE preferences SET confirmed = 1 WHERE category = ? AND key = ?",
            (category, key)
        )
        return cursor.rowcount > 0

def delete_preference(category: str, key: str) -> bool:
    """Delete a preference."""
    with db_session() as conn:
        cursor = conn.execute(
            "DELETE FROM preferences WHERE category = ? AND key = ?",
            (category, key)
        )
        return cursor.rowcount > 0