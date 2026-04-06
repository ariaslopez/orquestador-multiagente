"""Cliente para conectarse con crypto-intelligence-hub via Supabase compartido y APIs.

Esta integracion lee/escribe en las mismas tablas de Supabase que usa el hub,
permitiendo que el orquestador enriquezca el hub con analisis y tesis.
"""
from __future__ import annotations
import os
import logging
from datetime import datetime
from typing import Any, Optional

logger = logging.getLogger(__name__)


class CryptoHubClient:
    """Interfaz de alto nivel para interactuar con el crypto-intelligence-hub."""

    def __init__(self):
        self._supabase = None
        self._initialized = False

    def _get_client(self):
        """Lazy init del cliente Supabase."""
        if not self._supabase:
            try:
                from supabase import create_client
                url = os.getenv('SUPABASE_URL')
                key = os.getenv('SUPABASE_KEY')
                if not url or not key:
                    raise ValueError('SUPABASE_URL y SUPABASE_KEY requeridos para hub integration')
                self._supabase = create_client(url, key)
                self._initialized = True
            except ImportError:
                raise ImportError('supabase-py requerido: pip install supabase')
        return self._supabase

    # ------------------------------------------------------------------
    # READ: Leer datos del hub
    # ------------------------------------------------------------------

    def get_latest_signals(self, limit: int = 10) -> list[dict]:
        """Obtiene las ultimas senales generadas por el hub."""
        try:
            client = self._get_client()
            result = (
                client.table('signals')
                .select('*')
                .order('created_at', desc=True)
                .limit(limit)
                .execute()
            )
            return result.data or []
        except Exception as e:
            logger.error(f'Error obteniendo senales del hub: {e}')
            return []

    def get_market_data(self, symbol: Optional[str] = None) -> list[dict]:
        """Obtiene datos de mercado almacenados por el hub."""
        try:
            client = self._get_client()
            query = client.table('market_data').select('*').order('timestamp', desc=True).limit(50)
            if symbol:
                query = query.eq('symbol', symbol.upper())
            result = query.execute()
            return result.data or []
        except Exception as e:
            logger.error(f'Error obteniendo market data: {e}')
            return []

    def get_bot_performance(self, bot_name: Optional[str] = None) -> list[dict]:
        """Obtiene metricas de performance de los bots del hub."""
        try:
            client = self._get_client()
            query = client.table('bot_performance').select('*').order('created_at', desc=True).limit(100)
            if bot_name:
                query = query.eq('bot_name', bot_name)
            result = query.execute()
            return result.data or []
        except Exception as e:
            logger.error(f'Error obteniendo performance de bots: {e}')
            return []

    def get_published_content(self, limit: int = 20) -> list[dict]:
        """Obtiene contenido publicado por el hub."""
        try:
            client = self._get_client()
            result = (
                client.table('published_content')
                .select('*')
                .order('created_at', desc=True)
                .limit(limit)
                .execute()
            )
            return result.data or []
        except Exception as e:
            logger.error(f'Error obteniendo contenido publicado: {e}')
            return []

    # ------------------------------------------------------------------
    # WRITE: Enriquecer el hub con outputs del orquestador
    # ------------------------------------------------------------------

    def store_thesis(self, asset: str, thesis: str, metadata: Optional[dict] = None) -> bool:
        """Almacena una tesis de inversion generada por el orquestador en el hub."""
        try:
            client = self._get_client()
            record = {
                'asset': asset.upper(),
                'thesis': thesis,
                'source': 'orquestador-multiagente',
                'created_at': datetime.utcnow().isoformat(),
                'metadata': metadata or {},
            }
            client.table('investment_theses').insert(record).execute()
            logger.info(f'Tesis almacenada en hub para {asset}')
            return True
        except Exception as e:
            logger.error(f'Error almacenando tesis en hub: {e}')
            return False

    def store_analysis(self, analysis_type: str, content: str, metadata: Optional[dict] = None) -> bool:
        """Almacena un analisis generado por el orquestador."""
        try:
            client = self._get_client()
            record = {
                'type': analysis_type,
                'content': content,
                'source': 'orquestador-multiagente',
                'created_at': datetime.utcnow().isoformat(),
                'metadata': metadata or {},
            }
            client.table('orchestrator_outputs').upsert(record).execute()
            return True
        except Exception as e:
            logger.error(f'Error almacenando analisis: {e}')
            return False

    def update_bot_parameters(
        self,
        bot_name: str,
        parameters: dict,
        reason: str = '',
    ) -> bool:
        """Actualiza parametros de un bot del hub basado en analisis del orquestador."""
        try:
            client = self._get_client()
            record = {
                'bot_name': bot_name,
                'parameters': parameters,
                'reason': reason,
                'updated_by': 'orquestador-multiagente',
                'updated_at': datetime.utcnow().isoformat(),
            }
            client.table('bot_parameter_updates').insert(record).execute()
            logger.info(f'Parametros de {bot_name} actualizados en hub')
            return True
        except Exception as e:
            logger.error(f'Error actualizando parametros de bot: {e}')
            return False

    # ------------------------------------------------------------------
    # HEALTH CHECK
    # ------------------------------------------------------------------

    def health_check(self) -> dict:
        """Verifica conexion con el hub."""
        try:
            client = self._get_client()
            result = client.table('market_data').select('id').limit(1).execute()
            return {'status': 'connected', 'hub': 'crypto-intelligence-hub', 'records_found': len(result.data or [])}
        except Exception as e:
            return {'status': 'error', 'hub': 'crypto-intelligence-hub', 'error': str(e)}
