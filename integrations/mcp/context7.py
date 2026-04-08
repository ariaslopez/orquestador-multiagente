"""MCP Adaptador — Context7.

Provee documentacion tecnica actualizada de librerias y frameworks.
Util para CoderAgent y PlannerAgent cuando necesitan saber la API
exacta de una libreria (FastAPI, Supabase, Groq, etc.).

Herramientas disponibles:
  get_docs(library, topic='', version='latest')
    -> {library, version, topic, content, source_url}

Env requerida: CONTEXT7_API_KEY
Docs: https://context7.com/docs
"""
from __future__ import annotations
import os
import aiohttp
import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)

CONTEXT7_ENDPOINT = "https://api.context7.com/v1/docs"


class Context7Adapter:
    async def call(self, tool: str, params: Dict[str, Any]) -> Any:
        if tool == "get_docs":
            return await self._get_docs(**params)
        if tool == "resolve_library":
            return await self._resolve_library(**params)
        raise ValueError(f"Context7: tool '{tool}' desconocida")

    async def _get_docs(
        self,
        library: str,
        topic: str = "",
        version: str = "latest",
    ) -> Dict:
        api_key = os.getenv("CONTEXT7_API_KEY", "")
        headers = {"Authorization": f"Bearer {api_key}", "Accept": "application/json"}
        payload = {"library": library, "topic": topic, "version": version}

        async with aiohttp.ClientSession() as session:
            async with session.post(
                CONTEXT7_ENDPOINT, json=payload, headers=headers,
                timeout=aiohttp.ClientTimeout(total=20)
            ) as resp:
                resp.raise_for_status()
                data = await resp.json()

        logger.debug(f"Context7: docs '{library}/{topic}' obtenidos")
        return {
            "library":    data.get("library", library),
            "version":    data.get("version", version),
            "topic":      topic,
            "content":    data.get("content", ""),
            "source_url": data.get("source_url", ""),
        }

    async def _resolve_library(self, query: str) -> Dict:
        """Resuelve el nombre exacto de una libreria a partir de un query libre."""
        api_key = os.getenv("CONTEXT7_API_KEY", "")
        headers = {"Authorization": f"Bearer {api_key}"}
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://api.context7.com/v1/resolve",
                params={"q": query},
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                resp.raise_for_status()
                return await resp.json()


def get_adapter() -> Context7Adapter:
    return Context7Adapter()
