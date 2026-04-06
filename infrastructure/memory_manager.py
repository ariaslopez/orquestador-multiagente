"""MemoryManager — Persistencia dual: SQLite local + Supabase cloud."""
from __future__ import annotations
import os
import json
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

DB_PATH = Path(os.getenv('SQLITE_DB_PATH', 'data/claw_memory.db'))


class MemoryManager:
    def __init__(self):
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        self._init_sqlite()
        self._supabase = self._init_supabase()

    def _init_sqlite(self) -> None:
        conn = self._conn()
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                session_id TEXT UNIQUE NOT NULL,
                user_input TEXT,
                task_type TEXT,
                status TEXT DEFAULT 'running',
                final_output TEXT,
                total_tokens INTEGER DEFAULT 0,
                estimated_cost_usd REAL DEFAULT 0.0,
                duration_seconds REAL DEFAULT 0.0,
                output_path TEXT,
                metadata TEXT,
                created_at TEXT,
                updated_at TEXT
            );
            CREATE TABLE IF NOT EXISTS checkpoints (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                agent_name TEXT,
                context_json TEXT,
                created_at TEXT
            );
        """)
        conn.commit()
        conn.close()

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_supabase(self):
        url = os.getenv('SUPABASE_URL', '')
        key = os.getenv('SUPABASE_KEY', '')
        if url and key and 'your_' not in url:
            try:
                from supabase import create_client
                return create_client(url, key)
            except ImportError:
                pass
        return None

    def create_session(self, user_input: str, task_type: str = '') -> str:
        session_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        conn = self._conn()
        conn.execute(
            "INSERT INTO sessions (id, session_id, user_input, task_type, created_at, updated_at) VALUES (?,?,?,?,?,?)",
            (session_id, session_id, user_input, task_type, now, now)
        )
        conn.commit()
        conn.close()
        return session_id

    def update_session(self, session_id: str, **kwargs) -> None:
        if not kwargs:
            return
        kwargs['updated_at'] = datetime.utcnow().isoformat()
        fields = ', '.join(f"{k} = ?" for k in kwargs)
        values = list(kwargs.values()) + [session_id]
        conn = self._conn()
        conn.execute(f"UPDATE sessions SET {fields} WHERE session_id = ?", values)
        conn.commit()
        conn.close()
        if self._supabase:
            try:
                self._supabase.table('sessions').upsert({'session_id': session_id, **kwargs}).execute()
            except Exception:
                pass

    def save_checkpoint(self, session_id: str, agent_name: str, context_data: dict) -> None:
        cp_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        conn = self._conn()
        conn.execute(
            "INSERT INTO checkpoints (id, session_id, agent_name, context_json, created_at) VALUES (?,?,?,?,?)",
            (cp_id, session_id, agent_name, json.dumps(context_data, default=str), now)
        )
        conn.commit()
        conn.close()

    def get_all_sessions(self, limit: int = 20) -> List[Dict]:
        conn = self._conn()
        rows = conn.execute(
            "SELECT * FROM sessions ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_usage_stats(self) -> Dict[str, Any]:
        conn = self._conn()
        row = conn.execute("""
            SELECT COUNT(*) as total_sessions,
                   SUM(total_tokens) as total_tokens,
                   SUM(estimated_cost_usd) as total_cost_usd,
                   AVG(duration_seconds) as avg_duration
            FROM sessions WHERE status = 'completed'
        """).fetchone()
        conn.close()
        return dict(row) if row else {}
