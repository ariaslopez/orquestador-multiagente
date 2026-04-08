"""
DataAgent — Obtiene datos de mercado para el pipeline TRADING.

Estrategia:
  1. coingecko MCP → datos premium (OHLCV, precio, volumen, market cap)
  2. Fallback: CoinGecko REST API pública (sin API key, rate-limited)
  3. Snapshot opcional en supabase_mcp si está disponible

Outputs en ctx:
  - ctx.data['market_data']     : {symbol, price_usd, change_24h, volume_24h, market_cap}
  - ctx.data['market_snapshot'] : lista de OHLCV [{t, o, h, l, c, v}, ...]
  - ctx.data['market_provider'] : 'coingecko_mcp' | 'coingecko_rest' | 'none'
  - ctx.data['market_symbol']   : símbolo normalizado (ej: 'bitcoin')
"""
from __future__ import annotations
import logging
import re
from core.base_agent import BaseAgent
from core.context import AgentContext

logger = logging.getLogger(__name__)

# Mapa de alias comunes a IDs de CoinGecko
SYMBOL_MAP = {
    "btc": "bitcoin", "bitcoin": "bitcoin",
    "eth": "ethereum", "ethereum": "ethereum",
    "sol": "solana", "solana": "solana",
    "bnb": "binancecoin", "xrp": "ripple",
    "ada": "cardano", "doge": "dogecoin",
    "avax": "avalanche-2", "dot": "polkadot",
    "matic": "matic-network", "link": "chainlink",
}


def _extract_symbol(text: str) -> str:
    """Extrae el símbolo de crypto del input del usuario."""
    text_lower = text.lower()
    for alias, cg_id in SYMBOL_MAP.items():
        if alias in text_lower:
            return cg_id
    # buscar patrón de 3-5 letras mayusculas (ej: BTC, ETH, SOL)
    match = re.search(r"\b([A-Z]{2,5})\b", text)
    if match:
        return SYMBOL_MAP.get(match.group(1).lower(), match.group(1).lower())
    return "bitcoin"  # default


class DataAgent(BaseAgent):
    name = "DataAgent"
    description = "Obtiene datos de mercado cripto: precio, volumen, OHLCV. Soporta coingecko MCP."

    async def run(self, ctx: AgentContext) -> AgentContext:
        symbol = _extract_symbol(ctx.user_input)
        self.log(ctx, f"[DataAgent] símbolo detectado: {symbol}")

        market_data = {}
        snapshot = []
        provider = "none"

        # --- Estrategia 1: coingecko MCP ---
        if ctx.is_mcp_available("coingecko"):
            try:
                raw = await ctx.mcp_call(
                    "coingecko",
                    "get_coin_data",
                    {"coin_id": symbol, "vs_currency": "usd"},
                )
                market_data = {
                    "symbol": symbol,
                    "price_usd": raw.get("current_price", {}).get("usd"),
                    "change_24h": raw.get("price_change_percentage_24h"),
                    "volume_24h": raw.get("total_volume", {}).get("usd"),
                    "market_cap": raw.get("market_cap", {}).get("usd"),
                    "last_updated": raw.get("last_updated"),
                }
                provider = "coingecko_mcp"
                self.log(ctx, f"[DataAgent] coingecko MCP: ${market_data.get('price_usd')}")
            except Exception as exc:
                logger.warning("[DataAgent] coingecko MCP falló: %s — usando REST", exc)

        # --- Estrategia 2: CoinGecko REST fallback ---
        if not market_data:
            try:
                import httpx
                url = f"https://api.coingecko.com/api/v3/coins/{symbol}"
                params = {"localization": "false", "tickers": "false", "community_data": "false"}
                async with httpx.AsyncClient(timeout=10) as client:
                    resp = await client.get(url, params=params)
                    resp.raise_for_status()
                    raw = resp.json()
                market_data = {
                    "symbol": symbol,
                    "price_usd": raw.get("market_data", {}).get("current_price", {}).get("usd"),
                    "change_24h": raw.get("market_data", {}).get("price_change_percentage_24h"),
                    "volume_24h": raw.get("market_data", {}).get("total_volume", {}).get("usd"),
                    "market_cap": raw.get("market_data", {}).get("market_cap", {}).get("usd"),
                    "last_updated": raw.get("last_updated"),
                }
                provider = "coingecko_rest"
                self.log(ctx, f"[DataAgent] REST: ${market_data.get('price_usd')}")
            except Exception as exc:
                self.log(ctx, f"⚠ CoinGecko REST error: {exc}")

        # --- Opcional: guardar snapshot en Supabase ---
        if market_data and ctx.is_mcp_available("supabase_mcp"):
            try:
                await ctx.mcp_call(
                    "supabase_mcp",
                    "insert",
                    {
                        "table": "market_snapshots",
                        "data": {**market_data, "provider": provider},
                    },
                )
                self.log(ctx, "[DataAgent] snapshot guardado en Supabase")
            except Exception as exc:
                logger.debug("[DataAgent] Supabase snapshot omitido: %s", exc)

        ctx.set_data("market_data", market_data)
        ctx.set_data("market_snapshot", snapshot)
        ctx.set_data("market_provider", provider)
        ctx.set_data("market_symbol", symbol)

        if market_data:
            self.log(ctx, f"[DataAgent] ✓ {symbol} ${market_data.get('price_usd')} via {provider}")
        else:
            self.log(ctx, f"[DataAgent] ⚠ sin datos para {symbol}")

        return ctx
