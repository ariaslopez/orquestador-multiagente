"""CLAW MCP Integrations — 13 adaptadores MCP.

Disponibles:
  Search/Research : brave_search, context7, deepwiki
  Data/Memory     : supabase_mcp, mcp_memory, sequential_thinking
  Trading/Crypto  : coingecko, okx
  Dev/QA          : github_mcp, semgrep, playwright
  Automation      : slack, n8n

Uso desde cualquier agente:
    result = await ctx.mcp.call("brave_search", "search", {"query": "..."})
"""
