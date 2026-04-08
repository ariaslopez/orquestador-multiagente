"""MCP Adaptador — DeepWiki.

Analisis profundo de repositorios GitHub: estructura, patrones,
dependencias, decisiones arquitecturales y documentacion generada.
Util para QAAgent, SecurityAgent y CoderAgent cuando trabajan con repos.

Herramientas disponibles:
  analyze_repo(repo, focus='architecture')
    -> {summary, architecture, dependencies, patterns, issues}
  get_file_summary(repo, path)
    -> {path, summary, key_functions, complexity}

Env requerida: DEEPWIKI_API_KEY
Docs: https://deepwiki.com/api
"""
from __future__ import annotations
import os
import aiohttp
import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)

DEEPWIKI_ENDPOINT = "https://api.deepwiki.com/v1"


class DeepWikiAdapter:
    async def call(self, tool: str, params: Dict[str, Any]) -> Any:
        if tool == "analyze_repo":
            return await self._analyze_repo(**params)
        if tool == "get_file_summary":
            return await self._get_file_summary(**params)
        raise ValueError(f"DeepWiki: tool '{tool}' desconocida")

    async def _analyze_repo(
        self,
        repo: str,
        focus: str = "architecture",
    ) -> Dict:
        """Analiza un repositorio GitHub completo."""
        api_key = os.getenv("DEEPWIKI_API_KEY", "")
        headers = {"Authorization": f"Bearer {api_key}", "Accept": "application/json"}
        payload = {"repo": repo, "focus": focus}

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{DEEPWIKI_ENDPOINT}/analyze",
                json=payload, headers=headers,
                timeout=aiohttp.ClientTimeout(total=60),  # repos grandes tardan
            ) as resp:
                resp.raise_for_status()
                data = await resp.json()

        logger.debug(f"DeepWiki: analisis de '{repo}' completado")
        return {
            "repo":          repo,
            "summary":       data.get("summary", ""),
            "architecture":  data.get("architecture", ""),
            "dependencies":  data.get("dependencies", []),
            "patterns":      data.get("patterns", []),
            "issues":        data.get("issues", []),
        }

    async def _get_file_summary(self, repo: str, path: str) -> Dict:
        api_key = os.getenv("DEEPWIKI_API_KEY", "")
        headers = {"Authorization": f"Bearer {api_key}"}
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{DEEPWIKI_ENDPOINT}/file",
                params={"repo": repo, "path": path},
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=20),
            ) as resp:
                resp.raise_for_status()
                return await resp.json()


def get_adapter() -> DeepWikiAdapter:
    return DeepWikiAdapter()
