"""
Example adapter: SQLite memory store.

Usage:
    python parley.py \
        --store-a memories.json \
        --store-b agent.db \
        --adapter-b adapters.sqlite_adapter.SQLiteAdapter

Expects a table called 'memories' with at least a 'content' column.
Other columns (type, created, updated) are optional but recommended.
"""

import sqlite3
import json
from datetime import datetime, timezone


class SQLiteAdapter:
    """Read/write memories from a SQLite database."""

    def read(self, path: str) -> list[dict]:
        conn = sqlite3.connect(path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Try to read from a 'memories' table
        try:
            cursor.execute("SELECT * FROM memories")
            rows = cursor.fetchall()
            memories = [dict(row) for row in rows]
        except sqlite3.OperationalError:
            # Table doesn't exist — try to find any table with a 'content' column
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row["name"] for row in cursor.fetchall()]
            memories = []
            for table in tables:
                cursor.execute(f"PRAGMA table_info({table})")
                columns = [col["name"] for col in cursor.fetchall()]
                if "content" in columns:
                    cursor.execute(f"SELECT * FROM {table}")
                    memories.extend(dict(row) for row in cursor.fetchall())
                    break

        conn.close()
        return memories

    def write(self, path: str, memories: list[dict]):
        conn = sqlite3.connect(path)
        cursor = conn.cursor()

        # Create table if not exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                type TEXT DEFAULT 'fact',
                source TEXT DEFAULT 'parley_sync',
                created TEXT,
                updated TEXT
            )
        """)

        # Clear and rewrite (simple approach for sync)
        cursor.execute("DELETE FROM memories")
        now = datetime.now(timezone.utc).isoformat()

        for m in memories:
            cursor.execute(
                "INSERT INTO memories (content, type, source, created, updated) VALUES (?, ?, ?, ?, ?)",
                (
                    m.get("content", str(m)),
                    m.get("type", "fact"),
                    m.get("source", "parley_sync"),
                    m.get("created", now),
                    m.get("updated", now),
                )
            )

        conn.commit()
        conn.close()
