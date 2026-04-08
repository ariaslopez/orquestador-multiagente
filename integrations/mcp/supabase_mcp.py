"""MCP Adaptador — Supabase MCP.

Permite a los agentes hacer queries SQL en lenguaje natural sobre
las tablas de Supabase del proyecto CLAW (sessions, agent_traces,
audit_events). Util para AnalyticsAgent y ReportDistributorAgent.

Herramientas disponibles:
  query(sql)                              -> [{row}, ...]
  natural_query(question, table='')       -> [{row}, ...] via RPC
  get_session_stats(days=7)               -> {stats}
  get_agent_performance(agent_name='')    -> [{metrics}]

Env requerida: SUPABASE_URL, SUPABASE_KEY
"""
from __future__ import annotations
import os
import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class SupabaseMCPAdapter:
    def __init__(self):
        self._client = None

    def _get_client(self):
        if self._client:
            return self._client
        url = os.getenv("SUPABASE_URL", "")
        key = os.getenv("SUPABASE_KEY", "")
        from supabase import create_client
        self._client = create_client(url, key)
        return self._client

    async def call(self, tool: str, params: Dict[str, Any]) -> Any:
        if tool == "query":
            return await self._query(**params)
        if tool == "natural_query":
            return await self._natural_query(**params)
        if tool == "get_session_stats":
            return await self._get_session_stats(**params)
        if tool == "get_agent_performance":
            return await self._get_agent_performance(**params)
        raise ValueError(f"SupabaseMCP: tool '{tool}' desconocida")

    async def _query(self, sql: str) -> List[Dict]:
        """Ejecuta SQL crudo via Supabase RPC."""
        client = self._get_client()
        result = client.rpc("exec_sql", {"query": sql}).execute()
        logger.debug(f"SupabaseMCP: query ejecutado ({len(result.data or [])} filas)")
        return result.data or []

    async def _natural_query(self, question: str, table: str = "") -> List[Dict]:
        """Query en lenguaje natural sobre una tabla especifica."""
        client = self._get_client()
        # Mapeo de preguntas comunes a queries SQL predefinidas
        question_lower = question.lower()
        if "sesiones" in question_lower or "sessions" in question_lower:
            result = client.table("sessions").select("*").order(
                "created_at", desc=True
            ).limit(10).execute()
        elif "trazas" in question_lower or "traces" in question_lower or "agentes" in question_lower:
            result = client.table("agent_traces").select("*").order(
                "created_at", desc=True
            ).limit(20).execute()
        elif table:
            result = client.table(table).select("*").limit(10).execute()
        else:
            return [{"message": "Query no reconocida. Especifica la tabla o usa sql directo."}]
        return result.data or []

    async def _get_session_stats(self, days: int = 7) -> Dict:
        """Estadisticas de sesiones de los ultimos N dias."""
        client = self._get_client()
        result = client.table("sessions").select(
            "task_type, status, total_tokens, estimated_cost_usd, duration_seconds"
        ).execute()
        rows = result.data or []
        total      = len(rows)
        completed  = sum(1 for r in rows if r.get("status") == "completed")
        total_tok  = sum(r.get("total_tokens", 0) for r in rows)
        total_cost = sum(r.get("estimated_cost_usd", 0) for r in rows)
        avg_dur    = sum(r.get("duration_seconds", 0) for r in rows) / max(total, 1)
        return {
            "total_sessions":   total,
            "completed":        completed,
            "success_rate":     round(completed / max(total, 1), 3),
            "total_tokens":     total_tok,
            "total_cost_usd":   round(total_cost, 4),
            "avg_duration_s":   round(avg_dur, 1),
        }

    async def _get_agent_performance(self, agent_name: str = "") -> List[Dict]:
        """Performance de agentes individuales desde agent_traces."""
        client = self._get_client()
        q = client.table("agent_traces").select("*")
        if agent_name:
            q = q.eq("agent_name", agent_name)
        result = q.order("created_at", desc=True).limit(50).execute()
        return result.data or []


def get_adapter() -> SupabaseMCPAdapter:
    return SupabaseMCPAdapter()
