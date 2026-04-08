"""MCP Adaptador — Slack.

Envio de reportes, alertas y notificaciones del sistema a Slack.
Usado por ReportDistributorAgent y AuditLogger para comunicar
resultados de pipelines y alertas criticas.

Herramientas disponibles:
  send_message(channel, text, blocks=None)     -> {ok, ts}
  send_report(channel, title, content, color)  -> {ok, ts}
  send_alert(channel, level, message)          -> {ok, ts}
  list_channels()                              -> [{id, name}]

Env requerida: SLACK_BOT_TOKEN
Permisos requeridos: chat:write, channels:read
"""
from __future__ import annotations
import os
import aiohttp
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

SLACK_API = "https://slack.com/api"


class SlackMCPAdapter:
    def _headers(self) -> Dict:
        token = os.getenv("SLACK_BOT_TOKEN", "")
        return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    async def call(self, tool: str, params: Dict[str, Any]) -> Any:
        if tool == "send_message": return await self._send_message(**params)
        if tool == "send_report":  return await self._send_report(**params)
        if tool == "send_alert":   return await self._send_alert(**params)
        if tool == "list_channels": return await self._list_channels()
        raise ValueError(f"Slack: tool '{tool}' desconocida")

    async def _send_message(
        self,
        channel: str,
        text: str,
        blocks: Optional[List] = None,
    ) -> Dict:
        payload = {"channel": channel, "text": text}
        if blocks:
            payload["blocks"] = blocks
        async with aiohttp.ClientSession() as s:
            async with s.post(
                f"{SLACK_API}/chat.postMessage",
                json=payload, headers=self._headers(),
                timeout=aiohttp.ClientTimeout(total=10),
            ) as r:
                data = await r.json()
        ok = data.get("ok", False)
        if not ok:
            logger.warning(f"Slack: error enviando mensaje: {data.get('error')}")
        return {"ok": ok, "ts": data.get("ts")}

    async def _send_report(
        self,
        channel: str,
        title: str,
        content: str,
        color: str = "#36a64f",
    ) -> Dict:
        """Envia un reporte formateado como attachment de Slack."""
        blocks = [
            {"type": "header", "text": {"type": "plain_text", "text": title}},
            {"type": "section", "text": {"type": "mrkdwn", "text": content[:3000]}},
            {"type": "divider"},
            {"type": "context", "elements": [{"type": "mrkdwn",
             "text": f"_Generado por CLAW Agent System_"}]},
        ]
        return await self._send_message(channel, title, blocks=blocks)

    async def _send_alert(
        self,
        channel: str,
        level: str,
        message: str,
    ) -> Dict:
        """Envia una alerta con emoji segun nivel."""
        icons = {"info": "ℹ️", "warning": "⚠️", "critical": "🚨", "success": "✅"}
        icon  = icons.get(level.lower(), "🔔")
        text  = f"{icon} *[{level.upper()}]* {message}"
        return await self._send_message(channel, text)

    async def _list_channels(self) -> List[Dict]:
        async with aiohttp.ClientSession() as s:
            async with s.get(
                f"{SLACK_API}/conversations.list",
                params={"limit": 50, "types": "public_channel,private_channel"},
                headers=self._headers(),
                timeout=aiohttp.ClientTimeout(total=10),
            ) as r:
                data = await r.json()
        return [{"id": c["id"], "name": c["name"]} for c in data.get("channels", [])]


def get_adapter() -> SlackMCPAdapter:
    return SlackMCPAdapter()
