"""MCP Adaptador — MCP Memory.

Memoria persistente semantica entre sesiones y agentes.
A diferencia de MemoryManager (que guarda sesiones completas),
MCP Memory guarda fragmentos de conocimiento clave (insights,
patrones encontrados, decisiones tomadas) para reutilizarlos.

Herramientas disponibles:
  store(key, value, tags=[])         -> {stored: True}
  retrieve(key)                      -> {key, value, created_at}
  search(query, limit=5)             -> [{key, value, relevance}]
  list_all(tag='')                   -> [{key, value, tags}]
  delete(key)                        -> {deleted: True}

Backend: SQLite local (data/mcp_memory.db) — no requiere config externa.
"""
from __future__ import annotations
import json
import sqlite3
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

MEMORY_DB = Path("data/mcp_memory.db")


class MCPMemoryAdapter:
    def __init__(self):
        MEMORY_DB.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(MEMORY_DB)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS memory (
                key        TEXT PRIMARY KEY,
                value      TEXT NOT NULL,
                tags       TEXT DEFAULT '[]',
                created_at TEXT,
                updated_at TEXT
            )
        """)
        conn.commit()
        conn.close()

    def _conn(self):
        c = sqlite3.connect(MEMORY_DB)
        c.row_factory = sqlite3.Row
        return c

    async def call(self, tool: str, params: Dict[str, Any]) -> Any:
        if tool == "store":
            return await self._store(**params)
        if tool == "retrieve":
            return await self._retrieve(**params)
        if tool == "search":
            return await self._search(**params)
        if tool == "list_all":
            return await self._list_all(**params)
        if tool == "delete":
            return await self._delete(**params)
        raise ValueError(f"MCPMemory: tool '{tool}' desconocida")

    async def _store(self, key: str, value: Any, tags: List[str] = None) -> Dict:
        now = datetime.utcnow().isoformat()
        conn = self._conn()
        conn.execute("""
            INSERT INTO memory (key, value, tags, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET
                value=excluded.value, tags=excluded.tags, updated_at=excluded.updated_at
        """, (key, json.dumps(value, default=str), json.dumps(tags or []), now, now))
        conn.commit()
        conn.close()
        logger.debug(f"MCPMemory: stored '{key}'")
        return {"stored": True, "key": key}

    async def _retrieve(self, key: str) -> Dict:
        conn = self._conn()
        row = conn.execute("SELECT * FROM memory WHERE key = ?", (key,)).fetchone()
        conn.close()
        if not row:
            return {"found": False, "key": key}
        return {
            "found":      True,
            "key":        row["key"],
            "value":      json.loads(row["value"]),
            "tags":       json.loads(row["tags"]),
            "created_at": row["created_at"],
        }

    async def _search(self, query: str, limit: int = 5) -> List[Dict]:
        """Busqueda simple por keywords en key y value."""
        conn = self._conn()
        rows = conn.execute(
            "SELECT * FROM memory WHERE LOWER(key) LIKE ? OR LOWER(value) LIKE ? LIMIT ?",
            (f"%{query.lower()}%", f"%{query.lower()}%", limit)
        ).fetchall()
        conn.close()
        return [{"key": r["key"], "value": json.loads(r["value"]), "tags": json.loads(r["tags"])} for r in rows]

    async def _list_all(self, tag: str = "") -> List[Dict]:
        conn = self._conn()
        if tag:
            rows = conn.execute(
                "SELECT * FROM memory WHERE tags LIKE ? ORDER BY updated_at DESC",
                (f'%"{tag}"%',)
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM memory ORDER BY updated_at DESC").fetchall()
        conn.close()
        return [{"key": r["key"], "value": json.loads(r["value"]), "tags": json.loads(r["tags"])} for r in rows]

    async def _delete(self, key: str) -> Dict:
        conn = self._conn()
        conn.execute("DELETE FROM memory WHERE key = ?", (key,))
        conn.commit()
        conn.close()
        return {"deleted": True, "key": key}


def get_adapter() -> MCPMemoryAdapter:
    return MCPMemoryAdapter()
