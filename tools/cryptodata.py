"""Herramienta de datos crypto: CoinGecko, DefiLlama, CryptoCompare (free tier).

Sin dependencias de pago. Usa solo endpoints publicos.
"""
from __future__ import annotations
import os
import time
import logging
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

COINGECKO_BASE = 'https://api.coingecko.com/api/v3'
DEFILLAMA_BASE = 'https://api.llama.fi'
CRYPTOCOMPARE_BASE = 'https://min-api.cryptocompare.com/data'

_RATE_LIMIT_SLEEP = 1.2  # segundos entre requests a CoinGecko free tier


class CryptoDataTool:
    """Wrapper unificado para APIs de datos crypto gratuitas."""

    def __init__(self):
        self._last_cg_request = 0.0
        self.cc_key = os.getenv('CRYPTOCOMPARE_API_KEY', '')

    def _cg_get(self, path: str, params: Optional[dict] = None) -> dict | list:
        """GET a CoinGecko con rate limiting."""
        now = time.time()
        elapsed = now - self._last_cg_request
        if elapsed < _RATE_LIMIT_SLEEP:
            time.sleep(_RATE_LIMIT_SLEEP - elapsed)
        try:
            resp = httpx.get(f'{COINGECKO_BASE}{path}', params=params, timeout=15)
            resp.raise_for_status()
            self._last_cg_request = time.time()
            return resp.json()
        except Exception as e:
            logger.error(f'CoinGecko error [{path}]: {e}')
            return {}

    # ------------------------------------------------------------------
    # CoinGecko
    # ------------------------------------------------------------------

    def get_price(self, coin_ids: list[str], vs_currencies: list[str] = None) -> dict:
        """Precios actuales de multiples coins."""
        currencies = ','.join(vs_currencies or ['usd', 'btc'])
        return self._cg_get('/simple/price', {
            'ids': ','.join(coin_ids),
            'vs_currencies': currencies,
            'include_24hr_change': 'true',
            'include_market_cap': 'true',
        })

    def get_coin_detail(self, coin_id: str) -> dict:
        """Detalle completo de un coin: descripcion, links, metricas, comunidad."""
        return self._cg_get(f'/coins/{coin_id}', {
            'localization': 'false',
            'tickers': 'false',
            'community_data': 'true',
            'developer_data': 'true',
        })

    def get_market_chart(self, coin_id: str, days: int = 30, vs_currency: str = 'usd') -> dict:
        """Precio historico para un coin (OHLCV-like)."""
        return self._cg_get(f'/coins/{coin_id}/market_chart', {
            'vs_currency': vs_currency,
            'days': days,
            'interval': 'daily' if days > 7 else 'hourly',
        })

    def get_top_coins(self, limit: int = 50, vs_currency: str = 'usd') -> list:
        """Top N coins por market cap."""
        return self._cg_get('/coins/markets', {
            'vs_currency': vs_currency,
            'order': 'market_cap_desc',
            'per_page': min(limit, 250),
            'page': 1,
            'sparkline': 'false',
            'price_change_percentage': '1h,24h,7d',
        })

    def get_trending(self) -> dict:
        """Trending coins en las ultimas 24h segun CoinGecko."""
        return self._cg_get('/search/trending')

    def get_global_data(self) -> dict:
        """Datos globales del mercado crypto: dominancia, market cap total, etc."""
        return self._cg_get('/global')

    def get_exchanges(self, limit: int = 10) -> list:
        """Top exchanges por volumen."""
        return self._cg_get('/exchanges', {'per_page': limit, 'page': 1})

    # ------------------------------------------------------------------
    # DefiLlama
    # ------------------------------------------------------------------

    def get_defi_tvl(self, protocol: Optional[str] = None) -> dict | list:
        """TVL de todos los protocolos DeFi o de uno especifico."""
        try:
            if protocol:
                resp = httpx.get(f'{DEFILLAMA_BASE}/protocol/{protocol}', timeout=15)
            else:
                resp = httpx.get(f'{DEFILLAMA_BASE}/protocols', timeout=15)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error(f'DefiLlama error: {e}')
            return {}

    def get_chain_tvl(self) -> list:
        """TVL por chain blockchain."""
        try:
            resp = httpx.get(f'{DEFILLAMA_BASE}/v2/chains', timeout=15)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error(f'DefiLlama chains error: {e}')
            return []

    def get_yields(self, limit: int = 50) -> list:
        """Yields de pools DeFi ordenados por APY."""
        try:
            resp = httpx.get('https://yields.llama.fi/pools', timeout=15)
            resp.raise_for_status()
            pools = resp.json().get('data', [])
            pools.sort(key=lambda x: x.get('apy', 0), reverse=True)
            return pools[:limit]
        except Exception as e:
            logger.error(f'DefiLlama yields error: {e}')
            return []

    # ------------------------------------------------------------------
    # CryptoCompare (free tier)
    # ------------------------------------------------------------------

    def get_news(self, categories: Optional[str] = None, limit: int = 20) -> list:
        """Ultimas noticias crypto de CryptoCompare."""
        try:
            params: dict = {'lang': 'EN', 'limit': limit}
            if categories:
                params['categories'] = categories
            if self.cc_key:
                params['api_key'] = self.cc_key
            resp = httpx.get(f'{CRYPTOCOMPARE_BASE}/v2/news/', params=params, timeout=15)
            resp.raise_for_status()
            return resp.json().get('Data', [])
        except Exception as e:
            logger.error(f'CryptoCompare news error: {e}')
            return []

    def get_social_stats(self, coin_id: int) -> dict:
        """Stats sociales de un coin (Twitter, Reddit, etc.) por ID de CryptoCompare."""
        try:
            params: dict = {'coinId': coin_id}
            if self.cc_key:
                params['api_key'] = self.cc_key
            resp = httpx.get(f'{CRYPTOCOMPARE_BASE}/social/coin/latest', params=params, timeout=15)
            resp.raise_for_status()
            return resp.json().get('Data', {})
        except Exception as e:
            logger.error(f'CryptoCompare social stats error: {e}')
            return {}

    # ------------------------------------------------------------------
    # Helper combinado para tesis de inversion
    # ------------------------------------------------------------------

    def get_full_asset_context(self, coin_id: str) -> dict:
        """Recopila todos los datos disponibles de un asset para analisis profundo."""
        logger.info(f'Recopilando contexto completo para {coin_id}...')
        return {
            'price_current': self.get_price([coin_id]),
            'detail': self.get_coin_detail(coin_id),
            'chart_30d': self.get_market_chart(coin_id, days=30),
            'chart_90d': self.get_market_chart(coin_id, days=90),
            'global': self.get_global_data(),
            'news': self.get_news(categories=coin_id.upper(), limit=10),
        }
