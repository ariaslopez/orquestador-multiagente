"""MCPHub — Cliente central para todos los servidores MCP de CLAW.

Arquitectura:
  MCPHub es el punto único de acceso a herramientas MCP.
  Cada agente lo recibe via ctx.mcp y puede llamar cualquier tool
  sin saber los detalles de implementación del servidor.

Uso desde un agente:
    # Busqueda web
    results = await ctx.mcp.call("brave_search", "search", {"query": "Bitcoin 2026"})

    # Documentacion tecnica
    docs = await ctx.mcp.call("context7", "get_docs", {"library": "fastapi", "topic": "routing"})

    # Razonamiento encadenado
    plan = await ctx.mcp.call("sequential_thinking", "think", {"problem": "...", "steps": 5})

    # Memoria persistente
    await ctx.mcp.call("mcp_memory", "store", {"key": "session_insight", "value": "..."})
    insight = await ctx.mcp.call("mcp_memory", "retrieve", {"key": "session_insight"})

    # Precio crypto
    price = await ctx.mcp.call("coingecko", "get_price", {"ids": "bitcoin,ethereum"})

Servidores registrados (13):
  Search:   brave_search, context7, deepwiki
  Data:     supabase_mcp, mcp_memory, sequential_thinking
  Trading:  coingecko, okx
  Dev/QA:   github_mcp, semgrep, playwright
  Auto:     slack, n8n
"""
from __future__ import annotations
import os
import json
import logging
import asyncio
from typing import Any, Dict, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

# Importaciones lazy de adaptadores
_ADAPTERS: Dict[str, Any] = {}


def _load_adapter(name: str):
    """Carga el adaptador MCP bajo demanda (lazy import)."""
    if name in _ADAPTERS:
        return _ADAPTERS[name]
    try:
        module_map = {
            "brave_search":       "integrations.mcp.brave_search",
            "context7":           "integrations.mcp.context7",
            "deepwiki":           "integrations.mcp.deepwiki",
            "supabase_mcp":       "integrations.mcp.supabase_mcp",
            "mcp_memory":         "integrations.mcp.mcp_memory",
            "sequential_thinking":"integrations.mcp.sequential_thinking",
            "coingecko":          "integrations.mcp.coingecko_mcp",
            "okx":                "integrations.mcp.okx_mcp",
            "github_mcp":         "integrations.mcp.github_mcp",
            "semgrep":            "integrations.mcp.semgrep_mcp",
            "playwright":         "integrations.mcp.playwright_mcp",
            "slack":              "integrations.mcp.slack_mcp",
            "n8n":                "integrations.mcp.n8n_mcp",
        }
        if name not in module_map:
            raise ImportError(f"MCP '{name}' no registrado")
        import importlib
        mod = importlib.import_module(module_map[name])
        adapter = mod.get_adapter()
        _ADAPTERS[name] = adapter
        return adapter
    except Exception as e:
        logger.warning(f"MCPHub: no pudo cargar adaptador '{name}': {e}")
        return None


class MCPHub:
    """
    Punto de acceso unificado a todos los servidores MCP.

    Caracteristicas:
    - Lazy loading: los adaptadores solo se instancian cuando se usan
    - Fallback: si un MCP falla, retorna None sin romper el agente
    - Logging: cada llamada queda registrada en claw.log
    - Timeout: cada tool call tiene timeout configurable (default 30s)
    """

    # Timeout por defecto para tool calls (segundos)
    DEFAULT_TIMEOUT = int(os.getenv("MCP_TIMEOUT", "30"))

    # MCPs disponibles con metadata
    REGISTRY: Dict[str, Dict] = {
        "brave_search":        {"category": "search",   "required_env": "BRAVE_API_KEY"},
        "context7":            {"category": "search",   "required_env": "CONTEXT7_API_KEY"},
        "deepwiki":            {"category": "search",   "required_env": "DEEPWIKI_API_KEY"},
        "supabase_mcp":        {"category": "data",     "required_env": "SUPABASE_URL"},
        "mcp_memory":          {"category": "memory",   "required_env": None},
        "sequential_thinking": {"category": "reasoning","required_env": None},
        "coingecko":           {"category": "trading",  "required_env": None},
        "okx":                 {"category": "trading",  "required_env": "OKX_API_KEY"},
        "github_mcp":          {"category": "dev",      "required_env": "GITHUB_TOKEN"},
        "semgrep":             {"category": "security", "required_env": None},
        "playwright":          {"category": "qa",       "required_env": None},
        "slack":               {"category": "notify",   "required_env": "SLACK_BOT_TOKEN"},
        "n8n":                 {"category": "automation","required_env": "N8N_WEBHOOK_URL"},
    }

    async def call(
        self,
        server: str,
        tool: str,
        params: Dict[str, Any] = None,
        timeout: Optional[int] = None,
    ) -> Any:
        """
        Llama una herramienta de un servidor MCP.

        Args:
            server:  Nombre del servidor MCP (ej: 'brave_search')
            tool:    Nombre de la herramienta (ej: 'search')
            params:  Parametros de la herramienta
            timeout: Timeout en segundos (default: MCP_TIMEOUT)

        Returns:
            Resultado de la herramienta, o None si falla
        """
        params = params or {}
        _timeout = timeout or self.DEFAULT_TIMEOUT

        # Verificar env requerido
        meta = self.REGISTRY.get(server, {})
        required_env = meta.get("required_env")
        if required_env:
            val = os.getenv(required_env, "")
            if not val or "your_" in val:
                logger.warning(
                    f"MCPHub: '{server}.{tool}' requiere {required_env} en .env — saltando"
                )
                return None

        adapter = _load_adapter(server)
        if adapter is None:
            return None

        try:
            result = await asyncio.wait_for(
                adapter.call(tool, params),
                timeout=_timeout,
            )
            logger.debug(f"MCPHub: {server}.{tool}({list(params.keys())}) → OK")
            return result
        except asyncio.TimeoutError:
            logger.warning(f"MCPHub: {server}.{tool} timeout ({_timeout}s)")
            return None
        except Exception as e:
            logger.warning(f"MCPHub: {server}.{tool} error: {e}")
            return None

    def available(self, category: str = None) -> list:
        """
        Lista los MCPs disponibles (con su env key configurada).
        Filtra opcionalmente por categoria.
        """
        result = []
        for name, meta in self.REGISTRY.items():
            if category and meta["category"] != category:
                continue
            env = meta.get("required_env")
            configured = True
            if env:
                val = os.getenv(env, "")
                configured = bool(val) and "your_" not in val
            if configured:
                result.append(name)
        return result

    def status(self) -> Dict[str, str]:
        """Retorna el estado de configuracion de todos los MCPs."""
        out = {}
        for name, meta in self.REGISTRY.items():
            env = meta.get("required_env")
            if not env:
                out[name] = "ready"  # no requiere config
            else:
                val = os.getenv(env, "")
                out[name] = "ready" if (val and "your_" not in val) else f"missing:{env}"
        return out


# Singleton global — se instancia una sola vez
_hub: Optional[MCPHub] = None


def get_mcp_hub() -> MCPHub:
    """Retorna el singleton MCPHub. Thread-safe para uso en main.py."""
    global _hub
    if _hub is None:
        _hub = MCPHub()
        ready = _hub.available()
        logger.info(f"MCPHub: {len(ready)}/13 MCPs listos — {ready}")
    return _hub
