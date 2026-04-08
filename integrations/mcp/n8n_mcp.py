"""MCP Adaptador — n8n.

Dispara workflows de automatizacion en n8n via webhooks.
Util para orquestar acciones externas desde los agentes CLAW:
enviar emails, actualizar Google Sheets, sincronizar CRM, etc.

Herramientas disponibles:
  trigger_workflow(workflow_name, payload={})  -> {execution_id, status}
  trigger_webhook(webhook_url, payload={})     -> {response}
  list_workflows()                             -> [{id, name, active}]

Env requerida: N8N_WEBHOOK_URL, N8N_API_KEY (opcional para listar workflows)
"""
from __future__ import annotations
import os
import aiohttp
import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class N8NMCPAdapter:
    def _base_url(self) -> str:
        url = os.getenv("N8N_WEBHOOK_URL", "")
        # Normalizar a base URL sin el path del webhook
        if "/webhook/" in url:
            return url.rsplit("/webhook/", 1)[0]
        return url.rstrip("/")

    async def call(self, tool: str, params: Dict[str, Any]) -> Any:
        if tool == "trigger_workflow": return await self._trigger_workflow(**params)
        if tool == "trigger_webhook":  return await self._trigger_webhook(**params)
        if tool == "list_workflows":   return await self._list_workflows()
        raise ValueError(f"n8n: tool '{tool}' desconocida")

    async def _trigger_workflow(
        self,
        workflow_name: str,
        payload: Dict = None,
    ) -> Dict:
        """Dispara un workflow por nombre via webhook."""
        base  = self._base_url()
        url   = f"{base}/webhook/{workflow_name}"
        return await self._trigger_webhook(webhook_url=url, payload=payload or {})

    async def _trigger_webhook(
        self,
        webhook_url: str,
        payload: Dict = None,
    ) -> Dict:
        payload = payload or {}
        async with aiohttp.ClientSession() as s:
            async with s.post(
                webhook_url, json=payload,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as r:
                try:
                    data = await r.json()
                except Exception:
                    data = {"raw": await r.text()}
        logger.debug(f"n8n: webhook disparado -> {webhook_url} | status={r.status}")
        return {"status": r.status, "response": data}

    async def _list_workflows(self) -> List[Dict]:
        """Lista workflows activos via n8n API REST."""
        base    = self._base_url()
        api_key = os.getenv("N8N_API_KEY", "")
        headers = {"X-N8N-API-KEY": api_key} if api_key else {}
        async with aiohttp.ClientSession() as s:
            async with s.get(
                f"{base}/api/v1/workflows",
                params={"active": "true"},
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as r:
                r.raise_for_status()
                data = await r.json()
        return [{"id": w["id"], "name": w["name"], "active": w.get("active", False)} for w in data.get("data", [])]


def get_adapter() -> N8NMCPAdapter:
    return N8NMCPAdapter()
