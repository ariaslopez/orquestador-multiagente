"""WebSearch — Busqueda web via DuckDuckGo (sin API key requerida)."""
from __future__ import annotations
from typing import List, Dict


def search(query: str, max_results: int = 10) -> List[Dict]:
    """Busca en la web y retorna lista de resultados."""
    try:
        from duckduckgo_search import DDGS
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                results.append({
                    'title': r.get('title', ''),
                    'body': r.get('body', ''),
                    'url': r.get('href', ''),
                })
        return results
    except ImportError:
        raise ImportError("Instala duckduckgo-search: pip install duckduckgo-search")
    except Exception as e:
        return [{'title': 'Error', 'body': str(e), 'url': ''}]


def search_news(query: str, max_results: int = 5) -> List[Dict]:
    """Busca noticias recientes."""
    try:
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            return list(ddgs.news(query, max_results=max_results))
    except Exception:
        return []
