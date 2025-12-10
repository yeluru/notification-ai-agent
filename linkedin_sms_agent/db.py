"""SQLite database operations for tracking seen notifications."""

import sqlite3
from typing import Set, Tuple, Optional


def init_db(db_path: str) -> sqlite3.Connection:
    """
    Initialize the database and create tables if they don't exist.
    
    Args:
        db_path: Path to the SQLite database file.
        
    Returns:
        A connection to the database.
    """
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS seen_items (
            id TEXT NOT NULL,
            source TEXT NOT NULL,
            first_seen_at TEXT NOT NULL,
            PRIMARY KEY (id, source)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS meta (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    """)
    conn.commit()
    return conn


def get_seen_ids(conn: sqlite3.Connection) -> Set[Tuple[str, str]]:
    """
    Retrieve all seen item IDs from the database.
    
    Args:
        conn: Database connection.
        
    Returns:
        A set of (id, source) tuples that have been seen.
    """
    cursor = conn.execute("SELECT id, source FROM seen_items")
    return {(row[0], row[1]) for row in cursor.fetchall()}


def mark_seen(conn: sqlite3.Connection, items: list[Tuple[str, str]]) -> None:
    """
    Mark items as seen in the database.
    
    Args:
        conn: Database connection.
        items: List of (id, source) tuples to mark as seen.
    """
    from datetime import datetime
    
    now = datetime.utcnow().isoformat() + "Z"
    conn.executemany(
        "INSERT OR IGNORE INTO seen_items (id, source, first_seen_at) VALUES (?, ?, ?)",
        [(item_id, source, now) for item_id, source in items]
    )
    conn.commit()


def get_meta(conn: sqlite3.Connection, key: str) -> Optional[str]:
    """
    Get a metadata value from the database.
    
    Args:
        conn: Database connection.
        key: Metadata key.
        
    Returns:
        The metadata value, or None if not found.
    """
    cursor = conn.execute("SELECT value FROM meta WHERE key = ?", (key,))
    row = cursor.fetchone()
    return row[0] if row else None


def set_meta(conn: sqlite3.Connection, key: str, value: str) -> None:
    """
    Set a metadata value in the database.
    
    Args:
        conn: Database connection.
        key: Metadata key.
        value: Metadata value.
    """
    conn.execute(
        "INSERT OR REPLACE INTO meta (key, value) VALUES (?, ?)",
        (key, value)
    )
    conn.commit()


def clear_seen_items(conn: sqlite3.Connection, source: Optional[str] = None) -> None:
    """
    Clear seen items from the database.
    
    Args:
        conn: Database connection.
        source: If provided, only clear items with this source (e.g., "email" or "rss").
                If None, clear all seen items.
    """
    if source:
        conn.execute("DELETE FROM seen_items WHERE source = ?", (source,))
    else:
        conn.execute("DELETE FROM seen_items")
    conn.commit()

