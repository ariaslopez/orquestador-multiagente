"""MemoryManager — Persistencia dual: SQLite local + Supabase cloud.

Cambios v2.2.2:
  - save_session(): loguea warning visible si Supabase falla
    (antes era except: pass totalmente silencioso).
  - _init_supabase(): loguea mensaje informativo al conectar.
  - Consistencia: mismo patrón de logging que AuditLogger.
"""
from __future__ import annotations
import os
import json
import sqlite3
import uuid
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

DB_PATH = Path(os.getenv("SQLITE_DB_PATH", "data/claw_memory.db"))


class MemoryManager:
    def __init__(self):
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        self._init_sqlite()
        self._supabase = self._init_supabase()

    def _init_sqlite(self) -> None:
        conn = self._conn()
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS sessions (
                id                 TEXT PRIMARY KEY,
                session_id         TEXT UNIQUE NOT NULL,
                user_input         TEXT,
                task_type          TEXT,
                status             TEXT DEFAULT 'running',
                final_output       TEXT,
                total_tokens       INTEGER DEFAULT 0,
                estimated_cost_usd REAL DEFAULT 0.0,
                duration_seconds   REAL DEFAULT 0.0,
                output_path        TEXT,
                metadata           TEXT,
                created_at         TEXT,
                updated_at         TEXT
            );
            CREATE TABLE IF NOT EXISTS checkpoints (
                id           TEXT PRIMARY KEY,
                session_id   TEXT NOT NULL,
                agent_name   TEXT,
                context_json TEXT,
                created_at   TEXT
            );
        """)
        conn.commit()
        conn.close()

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_supabase(self):
        url = os.getenv("SUPABASE_URL", "")
        key = os.getenv("SUPABASE_KEY", "")
        if url and key and "your_" not in url:
            try:
                from supabase import create_client
                client = create_client(url, key)
                logger.info("MemoryManager: Supabase conectado correctamente")
                return client
            except ImportError:
                logger.warning("MemoryManager: supabase no instalado, solo SQLite local")
            except Exception as e:
                logger.warning(f"MemoryManager: no pudo conectar Supabase — {e}")
        return None

    # ------------------------------------------------------------------
    # Métodos llamados por Maestro.run()
    # ------------------------------------------------------------------

    async def save_session(self, ctx) -> None:
        """
        Guarda o actualiza una sesión completa a partir de un AgentContext.
        1. SQLite local — siempre (garantizado)
        2. Supabase — si está configurado, loguea warning si falla
        """
        now  = datetime.utcnow().isoformat()
        data = ctx.to_dict()

        # 1. SQLite local — siempre
        conn = self._conn()
        conn.execute("""
            INSERT INTO sessions
                (id, session_id, user_input, task_type, status,
                 final_output, total_tokens, estimated_cost_usd,
                 duration_seconds, output_path, created_at, updated_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(session_id) DO UPDATE SET
                status             = excluded.status,
                final_output       = excluded.final_output,
                total_tokens       = excluded.total_tokens,
                estimated_cost_usd = excluded.estimated_cost_usd,
                duration_seconds   = excluded.duration_seconds,
                output_path        = excluded.output_path,
                updated_at         = excluded.updated_at
        """, (
            data.get("session_id", str(uuid.uuid4())),
            data.get("session_id"),
            data.get("user_input"),
            data.get("task_type"),
            data.get("status", "completed"),
            data.get("final_output"),
            data.get("total_tokens", 0),
            data.get("estimated_cost_usd", 0.0),
            data.get("duration_seconds", 0.0),
            data.get("output_path"),
            data.get("started_at", now),
            now,
        ))
        conn.commit()
        conn.close()

        # 2. Supabase sync — si está configurado
        if self._supabase:
            try:
                self._supabase.table("sessions").upsert({
                    "session_id":          data.get("session_id"),
                    "user_input":          data.get("user_input"),
                    "task_type":           data.get("task_type"),
                    "status":              data.get("status"),
                    "final_output":        data.get("final_output"),
                    "total_tokens":        data.get("total_tokens", 0),
                    "estimated_cost_usd":  data.get("estimated_cost_usd", 0.0),
                    "duration_seconds":    data.get("duration_seconds", 0.0),
                    "output_path":         data.get("output_path"),
                    "updated_at":          now,
                }).execute()
            except Exception as e:
                logger.warning(
                    f"MemoryManager: Supabase sync falló para sesión "
                    f"{data.get('session_id', '')[:8]} — {e} "
                    f"(datos guardados en SQLite local)"
                )

    async def find_similar(
        self,
        user_input: str,
        task_type: str,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Busca sesiones anteriores del mismo tipo de tarea por keywords.
        Fallback automático a últimas N sesiones del mismo tipo si no hay matches.
        """
        conn = self._conn()
        keywords = [w for w in user_input.lower().split() if len(w) > 4][:3]

        rows = []
        if keywords:
            like_clause = " OR ".join(["LOWER(user_input) LIKE ?" for _ in keywords])
            like_params = [f"%{kw}%" for kw in keywords]
            rows = conn.execute(f"""
                SELECT * FROM sessions
                WHERE  status = 'completed'
                  AND  ({like_clause})
                  AND  task_type = ?
                ORDER  BY created_at DESC
                LIMIT  ?
            """, like_params + [task_type, limit]).fetchall()

        if not rows:
            rows = conn.execute("""
                SELECT * FROM sessions
                WHERE  status = 'completed' AND task_type = ?
                ORDER  BY created_at DESC
                LIMIT  ?
            """, (task_type, limit)).fetchall()

        conn.close()
        return [dict(r) for r in rows]

    # ------------------------------------------------------------------
    # Métodos de consulta y mantenimiento
    # ------------------------------------------------------------------

    def create_session(self, user_input: str, task_type: str = "") -> str:
        session_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        conn = self._conn()
        conn.execute(
            "INSERT INTO sessions (id, session_id, user_input, task_type, "
            "created_at, updated_at) VALUES (?,?,?,?,?,?)",
            (session_id, session_id, user_input, task_type, now, now),
        )
        conn.commit()
        conn.close()
        return session_id

    def update_session(self, session_id: str, **kwargs) -> None:
        if not kwargs:
            return
        kwargs["updated_at"] = datetime.utcnow().isoformat()
        fields = ", ".join(f"{k} = ?" for k in kwargs)
        values = list(kwargs.values()) + [session_id]
        conn = self._conn()
        conn.execute(f"UPDATE sessions SET {fields} WHERE session_id = ?", values)
        conn.commit()
        conn.close()
        if self._supabase:
            try:
                self._supabase.table("sessions").upsert(
                    {"session_id": session_id, **kwargs}
                ).execute()
            except Exception as e:
                logger.debug(f"update_session Supabase sync falló: {e}")

    def save_checkpoint(self, session_id: str, agent_name: str, context_data: dict) -> None:
        cp_id = str(uuid.uuid4())
        now   = datetime.utcnow().isoformat()
        conn  = self._conn()
        conn.execute(
            "INSERT INTO checkpoints (id, session_id, agent_name, context_json, created_at) "
            "VALUES (?,?,?,?,?)",
            (cp_id, session_id, agent_name, json.dumps(context_data, default=str), now),
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
            SELECT COUNT(*)          AS total_sessions,
                   SUM(total_tokens) AS total_tokens,
                   SUM(estimated_cost_usd) AS total_cost_usd,
                   AVG(duration_seconds)   AS avg_duration
            FROM sessions WHERE status = 'completed'
        """).fetchone()
        conn.close()
        return dict(row) if row else {}
