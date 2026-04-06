"""MemoryManager — Memoria persistente: SQLite local + Supabase cloud sync."""
from __future__ import annotations
import os
import json
import logging
import sqlite3
from typing import Any, Dict, List, Optional
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class MemoryManager:
    """
    Gestiona la memoria del sistema en dos capas:
    1. SQLite local: rápido, sin latencia, disponible offline
    2. Supabase cloud: sincronización entre sesiones y máquinas
    """

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or os.getenv("LOCAL_DB_PATH", "./data/claw_memory.db")
        self._supabase = None
        self._db_conn = None
        self._init_local_db()

    def _init_local_db(self) -> None:
        """Crea las tablas SQLite si no existen."""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        conn = self._get_conn()
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                task_id TEXT,
                user_input TEXT,
                task_type TEXT,
                status TEXT,
                final_output TEXT,
                output_path TEXT,
                total_tokens INTEGER,
                cost_usd REAL,
                duration_seconds REAL,
                created_at TEXT,
                finished_at TEXT
            );

            CREATE TABLE IF NOT EXISTS agent_memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE NOT NULL,
                value TEXT,
                category TEXT,
                created_at TEXT,
                updated_at TEXT
            );

            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_name TEXT NOT NULL,
                path_local TEXT,
                task_type TEXT,
                description TEXT,
                status TEXT DEFAULT 'completed',
                created_at TEXT
            );

            CREATE TABLE IF NOT EXISTS research_store (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                asset TEXT NOT NULL,
                title TEXT,
                content TEXT,
                sources TEXT,
                created_at TEXT
            );

            CREATE TABLE IF NOT EXISTS content_store (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content_type TEXT,
                platform TEXT,
                content TEXT,
                created_at TEXT
            );

            CREATE TABLE IF NOT EXISTS checkpoints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                agent_name TEXT,
                data TEXT,
                created_at TEXT
            );
        """)
        conn.commit()
        logger.info(f"MemoryManager: SQLite inicializado en {self.db_path}")

    def _get_conn(self) -> sqlite3.Connection:
        if not self._db_conn:
            self._db_conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self._db_conn.row_factory = sqlite3.Row
        return self._db_conn

    def _get_supabase(self):
        if not self._supabase:
            try:
                from supabase import create_client
                url = os.getenv("SUPABASE_URL", "")
                key = os.getenv("SUPABASE_KEY", "")
                if url and key:
                    self._supabase = create_client(url, key)
                    logger.info("MemoryManager: Supabase conectado")
            except Exception as e:
                logger.warning(f"MemoryManager: Supabase no disponible: {e}")
        return self._supabase

    async def save_session(self, ctx) -> None:
        """Guarda una sesión completada en SQLite y sincroniza a Supabase."""
        data = ctx.to_dict()
        conn = self._get_conn()
        conn.execute("""
            INSERT OR REPLACE INTO sessions
            (id, task_id, user_input, task_type, status, final_output,
             output_path, total_tokens, cost_usd, duration_seconds, created_at, finished_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data["session_id"], data["task_id"], data["user_input"],
            data["task_type"], data["status"], data["final_output"],
            data["output_path"], data["total_tokens"], data["estimated_cost_usd"],
            data["duration_seconds"], data["started_at"], data["finished_at"],
        ))
        conn.commit()

        # Sync a Supabase (no bloqueante)
        supabase = self._get_supabase()
        if supabase:
            try:
                supabase.table("agent_sessions").upsert(data).execute()
            except Exception as e:
                logger.warning(f"Supabase sync falló: {e}")

    async def find_similar(self, user_input: str, task_type: str, limit: int = 3) -> List[Dict]:
        """Busca sesiones previas similares por tipo de tarea."""
        conn = self._get_conn()
        rows = conn.execute("""
            SELECT user_input, final_output, output_path, created_at
            FROM sessions
            WHERE task_type = ? AND status = 'completed'
            ORDER BY created_at DESC
            LIMIT ?
        """, (task_type, limit)).fetchall()
        return [dict(row) for row in rows]

    def save_project(self, name: str, path: str, task_type: str, description: str) -> None:
        conn = self._get_conn()
        conn.execute("""
            INSERT INTO projects (project_name, path_local, task_type, description, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (name, path, task_type, description, datetime.utcnow().isoformat()))
        conn.commit()

    def save_checkpoint(self, session_id: str, agent_name: str, data: Dict) -> None:
        conn = self._get_conn()
        conn.execute("""
            INSERT INTO checkpoints (session_id, agent_name, data, created_at)
            VALUES (?, ?, ?, ?)
        """, (session_id, agent_name, json.dumps(data), datetime.utcnow().isoformat()))
        conn.commit()

    def get_last_checkpoint(self, session_id: str) -> Optional[Dict]:
        conn = self._get_conn()
        row = conn.execute("""
            SELECT * FROM checkpoints WHERE session_id = ?
            ORDER BY created_at DESC LIMIT 1
        """, (session_id,)).fetchone()
        if row:
            r = dict(row)
            r["data"] = json.loads(r["data"])
            return r
        return None

    def get_all_sessions(self, limit: int = 50, task_type: Optional[str] = None) -> List[Dict]:
        conn = self._get_conn()
        if task_type:
            rows = conn.execute(
                "SELECT * FROM sessions WHERE task_type = ? ORDER BY created_at DESC LIMIT ?",
                (task_type, limit)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM sessions ORDER BY created_at DESC LIMIT ?",
                (limit,)
            ).fetchall()
        return [dict(row) for row in rows]

    def get_all_projects(self) -> List[Dict]:
        conn = self._get_conn()
        rows = conn.execute("SELECT * FROM projects ORDER BY created_at DESC").fetchall()
        return [dict(row) for row in rows]

    def get_usage_stats(self) -> Dict[str, Any]:
        conn = self._get_conn()
        row = conn.execute("""
            SELECT
                COUNT(*) as total_sessions,
                SUM(total_tokens) as total_tokens,
                SUM(cost_usd) as total_cost_usd,
                AVG(duration_seconds) as avg_duration
            FROM sessions
        """).fetchone()
        return dict(row) if row else {}
