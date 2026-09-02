import sqlite3
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from contextlib import contextmanager

# Assumes this is run from the root edith/ directory
DB_PATH = Path(__file__).parent.parent / "edith.db"

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