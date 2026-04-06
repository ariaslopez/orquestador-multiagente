"""DataAgent — Agrega datos de mercado crypto al contexto de investigación.

Este agente complementa al WebScoutAgent trayendo datos estructurados desde APIs
como CoinGecko/DeFiLlama via CryptoDataTool.
"""
from __future__ import annotations
from typing import Any, Dict
from core.base_agent import BaseAgent
from core.context import AgentContext
from tools.crypto_data import CryptoDataTool


class DataAgent(BaseAgent):
    name = "DataAgent"
    description = "Obtiene precios, métricas de mercado y protocolos DeFi relevantes."

    async def run(self, context: AgentContext) -> AgentContext:
        topic = context.user_input.lower()
        # Heurística simple para mapear a IDs de CoinGecko
        coin_id = getattr(context, "asset_id", None) or self._infer_coin_id(topic)

        tool = CryptoDataTool()
        market_snapshot: Dict[str, Any] = {}
        historical: Any = []
        trending: Any = []

        if coin_id:
            self.log(context, f"Obteniendo datos de mercado para: {coin_id}")
            price = await tool.get_price(coin_id)
            market = await tool.get_market_data(coin_id)
            hist = await tool.get_historical_prices(coin_id, days=30)
            market_snapshot = {
                "coin_id": coin_id,
                "price": price,
                "market": {
                    "symbol": market.get("symbol"),
                    "name": market.get("name"),
                    "categories": market.get("categories", []),
                    "market_cap_rank": market.get("market_cap_rank"),
                },
            }
            historical = hist
        else:
            self.log(context, "No se pudo inferir un asset_id claro, solo se obtendrán trending/DeFi.")

        trending = await tool.get_trending()
        defi = await tool.get_top_defi_protocols(limit=15)

        context.set_data("market_snapshot", market_snapshot)
        context.set_data("market_historical", historical)
        context.set_data("market_trending", trending)
        context.set_data("defi_protocols", defi)

        self.log(
            context,
            f"DataAgent completado: coin_id={coin_id or 'N/A'}, "
            f"trending={len(trending)}, defi={len(defi)}",
        )
        return context

    def _infer_coin_id(self, topic: str) -> str | None:
        # Map básicos para los principales activos; extensible en el futuro.
        mapping = {
            "btc": "bitcoin",
            "bitcoin": "bitcoin",
            "eth": "ethereum",
            "ethereum": "ethereum",
            "sol": "solana",
            "solana": "solana",
            "arb": "arbitrum",
            "arbitrum": "arbitrum",
            "op": "optimism",
            "optimism": "optimism",
            "base": "base",
        }
        for key, cid in mapping.items():
            if key in topic:
                return cid
        return None
