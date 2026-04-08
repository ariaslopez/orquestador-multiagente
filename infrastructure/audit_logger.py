"""AuditLogger — Registro completo de operaciones + sync Supabase.

Cambios v2.2.2:
  - log_agent_trace() sincroniza a tabla 'agent_traces' en Supabase.
  - log() sincroniza a tabla 'audit_events' en Supabase.
  - Singleton _supabase lazy (mismo patrón que MemoryManager).
  - Siempre escribe a archivos locales primero (fallback garantizado).
"""
from __future__ import annotations
import os
import json
import logging
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

LOG_PATH   = Path(os.getenv("AUDIT_LOG_PATH",  "data/security.log"))
TRACE_PATH = Path(os.getenv("TRACE_LOG_PATH",  "data/traces.log"))


class AuditLogger:
    """
    Registro de auditoría con persistencia dual:
      1. Archivos locales (data/security.log, data/traces.log) — siempre
      2. Supabase (agent_traces, audit_events) — si está configurado
    """

    _supabase = None   # singleton compartido por todas las instancias

    def __init__(self):
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        TRACE_PATH.parent.mkdir(parents=True, exist_ok=True)
        if AuditLogger._supabase is None:
            AuditLogger._supabase = self._connect_supabase()

    @staticmethod
    def _connect_supabase():
        url = os.getenv("SUPABASE_URL", "")
        key = os.getenv("SUPABASE_KEY", "")
        if url and key and "your_" not in url:
            try:
                from supabase import create_client
                client = create_client(url, key)
                logger.info("AuditLogger: Supabase conectado")
                return client
            except ImportError:
                logger.warning("AuditLogger: supabase no instalado, solo modo archivo")
            except Exception as e:
                logger.warning(f"AuditLogger: no pudo conectar Supabase — {e}")
        return None

    # ------------------------------------------------------------------
    # Escritura a archivo local (siempre funciona)
    # ------------------------------------------------------------------

    def _write(self, path: Path, entry: dict) -> None:
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, default=str) + "\n")

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    def log(
        self,
        event_type: str,
        actor: str,
        action: str,
        target: str = "",
        result: str = "ok",
        metadata: Optional[dict] = None,
    ) -> None:
        """Registra un evento de auditoría de seguridad."""
        entry = {
            "timestamp":  datetime.utcnow().isoformat(),
            "event_type": event_type,
            "actor":      actor,
            "action":     action,
            "target":     target,
            "result":     result,
            "metadata":   metadata or {},
        }
        # 1. Archivo local — siempre
        self._write(LOG_PATH, entry)

        # 2. Supabase — tabla audit_events (si está configurado)
        if self._supabase:
            try:
                self._supabase.table("audit_events").insert({
                    "event_type": event_type,
                    "actor":      actor,
                    "action":     action,
                    "target":     target,
                    "result":     result,
                    "metadata":   metadata or {},
                    "created_at": entry["timestamp"],
                }).execute()
            except Exception as e:
                logger.debug(f"AuditLogger.log Supabase sync falló: {e}")

    def log_agent_trace(
        self,
        agent_name: str,
        pipeline: str,
        session_id: str,
        duration_ms: float,
        tokens: int,
        cost_usd: float,
        status: str = "ok",
    ) -> None:
        """Registra métricas de tiempo, tokens y costo por agente individual."""
        now = datetime.utcnow().isoformat()
        entry = {
            "timestamp":   now,
            "event_type":  "AGENT_TRACE",
            "agent":       agent_name,
            "pipeline":    pipeline,
            "session_id":  session_id,
            "duration_ms": round(duration_ms, 2),
            "tokens":      tokens,
            "cost_usd":    round(cost_usd, 6),
            "status":      status,
        }
        # 1. Archivo local — siempre
        self._write(TRACE_PATH, entry)

        # 2. Supabase — tabla agent_traces
        if self._supabase:
            try:
                self._supabase.table("agent_traces").insert({
                    "session_id":  session_id,
                    "agent_name":  agent_name,
                    "pipeline":    pipeline,
                    "status":      status,
                    "duration_ms": round(duration_ms, 2),
                    "tokens":      tokens,
                    "cost_usd":    round(cost_usd, 6),
                    "created_at":  now,
                }).execute()
            except Exception as e:
                logger.debug(f"AuditLogger.log_agent_trace Supabase sync falló: {e}")

    # ------------------------------------------------------------------
    # Shortcuts
    # ------------------------------------------------------------------

    def log_file_write(self, agent: str, path: str, size_bytes: int) -> None:
        self.log("FILE_WRITE", agent, "write", path, "ok", {"size_bytes": size_bytes})

    def log_command(self, agent: str, command: str, allowed: bool) -> None:
        self.log("COMMAND_EXEC", agent, command, "", "ok" if allowed else "BLOCKED")

    def log_api_call(self, agent: str, url: str, model: str = "", tokens: int = 0) -> None:
        self.log("API_CALL", agent, "llm_request", url, "ok", {"model": model, "tokens": tokens})

    def log_security_violation(self, agent: str, violation: str, detail: str = "") -> None:
        self.log("SECURITY_VIOLATION", agent, violation, "", "BLOCKED", {"detail": detail})

    # ------------------------------------------------------------------
    # Analytics sobre archivos locales
    # ------------------------------------------------------------------

    def get_pipeline_stats(self, pipeline: str = None, limit: int = 100) -> dict:
        """Agrega métricas de trazas locales por pipeline."""
        if not TRACE_PATH.exists():
            return {}

        lines = TRACE_PATH.read_text(encoding="utf-8").strip().split("\n")
        stats: dict = defaultdict(
            lambda: {"calls": 0, "total_tokens": 0, "total_cost_usd": 0.0,
                     "total_duration_ms": 0.0, "errors": 0}
        )

        for line in lines[-limit:]:
            try:
                entry = json.loads(line)
                if entry.get("event_type") != "AGENT_TRACE":
                    continue
                pipe = entry.get("pipeline", "unknown")
                if pipeline and pipe != pipeline:
                    continue
                s = stats[pipe]
                s["calls"]            += 1
                s["total_tokens"]     += entry.get("tokens", 0)
                s["total_cost_usd"]   += entry.get("cost_usd", 0.0)
                s["total_duration_ms"] += entry.get("duration_ms", 0.0)
                if entry.get("status") != "ok":
                    s["errors"] += 1
            except Exception:
                pass

        result = {}
        for pipe, s in stats.items():
            calls = s["calls"] or 1
            result[pipe] = {
                "calls":          s["calls"],
                "total_tokens":   s["total_tokens"],
                "total_cost_usd": round(s["total_cost_usd"], 6),
                "avg_duration_ms": round(s["total_duration_ms"] / calls, 1),
                "error_rate":     round(s["errors"] / calls, 3),
            }
        return result

    def get_most_used_pipeline(self) -> str:
        stats = self.get_pipeline_stats()
        if not stats:
            return "unknown"
        return max(stats, key=lambda p: stats[p]["calls"])

    def get_recent_logs(self, limit: int = 50) -> list:
        if not LOG_PATH.exists():
            return []
        lines = LOG_PATH.read_text(encoding="utf-8").strip().split("\n")
        entries = []
        for line in lines[-limit:]:
            try:
                entries.append(json.loads(line))
            except Exception:
                pass
        return entries
