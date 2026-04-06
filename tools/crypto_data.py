"""CryptoDataTool — Obtiene datos de mercado crypto en tiempo real."""
from __future__ import annotations
import logging
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


class CryptoDataTool:
    """
    Obtiene datos crypto desde:
    - CoinGecko API (gratis, sin key)
    - DeFiLlama (TVL, protocolos DeFi)
    """

    COINGECKO_BASE = "https://api.coingecko.com/api/v3"
    DEFILLAMA_BASE = "https://api.llama.fi"

    def __init__(self):
        self._session = None

    async def _get(self, url: str, params: Optional[Dict] = None) -> Dict:
        """Realiza una petición GET asíncrona."""
        import httpx
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(url, params=params or {})
            response.raise_for_status()
            return response.json()

    async def get_price(self, coin_id: str, currency: str = "usd") -> Dict[str, Any]:
        """Obtiene precio actual, cambio 24h, market cap y volumen."""
        try:
            data = await self._get(
                f"{self.COINGECKO_BASE}/simple/price",
                params={
                    "ids": coin_id,
                    "vs_currencies": currency,
                    "include_market_cap": "true",
                    "include_24hr_vol": "true",
                    "include_24hr_change": "true",
                }
            )
            return data.get(coin_id, {})
        except Exception as e:
            logger.error(f"CryptoData.get_price error: {e}")
            return {}

    async def get_market_data(self, coin_id: str) -> Dict:
        """Obtiene datos completos de mercado para un activo."""
        try:
            return await self._get(f"{self.COINGECKO_BASE}/coins/{coin_id}")
        except Exception as e:
            logger.error(f"CryptoData.get_market_data error: {e}")
            return {}

    async def get_historical_prices(
        self,
        coin_id: str,
        days: int = 30,
        currency: str = "usd",
    ) -> List[List[float]]:
        """Retorna precios históricos: [[timestamp_ms, price], ...]"""
        try:
            data = await self._get(
                f"{self.COINGECKO_BASE}/coins/{coin_id}/market_chart",
                params={"vs_currency": currency, "days": days, "interval": "daily"},
            )
            return data.get("prices", [])
        except Exception as e:
            logger.error(f"CryptoData.get_historical error: {e}")
            return []

    async def get_top_defi_protocols(self, limit: int = 20) -> List[Dict]:
        """Obtiene los top protocolos DeFi por TVL desde DeFiLlama."""
        try:
            data = await self._get(f"{self.DEFILLAMA_BASE}/protocols")
            sorted_data = sorted(data, key=lambda x: x.get("tvl", 0), reverse=True)
            return sorted_data[:limit]
        except Exception as e:
            logger.error(f"CryptoData.get_defi_protocols error: {e}")
            return []

    async def get_trending(self) -> List[Dict]:
        """Obtiene las criptomonedas trending del momento."""
        try:
            data = await self._get(f"{self.COINGECKO_BASE}/search/trending")
            return data.get("coins", [])
        except Exception as e:
            logger.error(f"CryptoData.get_trending error: {e}")
            return []
