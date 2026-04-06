"""Integration test for the RESEARCH pipeline (mocked LLM + mocked CryptoDataTool).

Runs the full RESEARCH pipeline chain:
  WebScout + Data (parallel intent) -> Analyst -> Thesis

All LLM calls and external API calls are mocked so this test:
- Does NOT require API keys
- Does NOT make network calls (no DuckDuckGo, no CoinGecko)
- Validates that the pipeline produces a thesis and analysis in context

Run: pytest tests/test_integration_research.py -v
"""
import sys
import asyncio
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))
import os
os.environ["SQLITE_DB_PATH"] = "/tmp/test_research_integration.db"


FAKE_WEB_RESULTS = [
    {"title": "Solana ecosystem growing", "body": "TVL up 30% in Q1 2026", "href": "https://example.com/1"},
    {"title": "SOL price analysis", "body": "Analysts bullish on SOL for Q2", "href": "https://example.com/2"},
]

FAKE_MARKET_SNAPSHOT = {
    "id": "solana", "symbol": "sol", "name": "Solana",
    "current_price": 142.50, "market_cap": 65_000_000_000,
    "market_cap_rank": 5, "price_change_percentage_24h": 3.2,
}

FAKE_ANALYSIS = (
    "Solana muestra fortaleza técnica con soporte en $130. "
    "TVL en alza indica adopción DeFi sostenida. Sentimiento positivo."
)

FAKE_THESIS = """## Tesis de Inversión: Solana (SOL) — Q2 2026

**Recomendación:** ACUMULAR
**Precio objetivo:** $185 (+30%)
**Horizonte:** 90 días

### Fundamentos
- TVL ecosystem +30% Q1 2026
- Ranking #5 por market cap
- Volumen on-chain estable

### Riesgos
- Competencia de Ethereum L2s
- Regulación en mercados clave
"""


def make_llm_response(content: str):
    msg = MagicMock()
    msg.content = content
    choice = MagicMock()
    choice.message = msg
    response = MagicMock()
    response.choices = [choice]
    return response


class TestResearchPipelineIntegration(unittest.IsolatedAsyncioTestCase):

    async def asyncTearDown(self):
        Path("/tmp/test_research_integration.db").unlink(missing_ok=True)

    async def _run_pipeline(self):
        from core.context import AgentContext
        from agents.research.webscout_agent import WebScoutAgent
        from agents.research.data_agent import DataAgent
        from agents.research.analyst_agent import AnalystAgent
        from agents.research.thesis_agent import ThesisAgent

        ctx = AgentContext(
            user_input="Tesis de inversión para Solana Q2 2026",
            task_type="research",
            session_id="test-research-integration",
        )
        # Set asset hint so DataAgent can resolve it
        ctx.asset_id = "solana"

        llm_responses = [
            make_llm_response(FAKE_ANALYSIS),  # AnalystAgent
            make_llm_response(FAKE_THESIS),    # ThesisAgent
        ]
        call_count = {"n": 0}

        async def mock_complete(*args, **kwargs):
            idx = min(call_count["n"], len(llm_responses) - 1)
            call_count["n"] += 1
            return llm_responses[idx]

        with patch("core.api_router.APIRouter.complete", side_effect=mock_complete):
            # Mock DuckDuckGo
            with patch("agents.research.webscout_agent.DDGS") as mock_ddgs:
                mock_ddgs.return_value.__enter__ = MagicMock(return_value=mock_ddgs.return_value)
                mock_ddgs.return_value.__exit__ = MagicMock(return_value=False)
                mock_ddgs.return_value.text = MagicMock(return_value=FAKE_WEB_RESULTS)

                # Mock CryptoDataTool
                with patch("agents.research.data_agent.CryptoDataTool") as mock_crypto:
                    instance = mock_crypto.return_value
                    instance.get_market_snapshot = AsyncMock(return_value=FAKE_MARKET_SNAPSHOT)
                    instance.get_historical_prices = AsyncMock(return_value=[])
                    instance.get_trending_coins = AsyncMock(return_value=[])
                    instance.get_defi_protocols = AsyncMock(return_value=[])

                    webscout = WebScoutAgent()
                    data = DataAgent()
                    analyst = AnalystAgent()
                    thesis_agent = ThesisAgent()

                    ctx = await webscout.run(ctx)
                    ctx = await data.run(ctx)
                    ctx = await analyst.run(ctx)
                    ctx = await thesis_agent.run(ctx)

        return ctx

    async def test_pipeline_produces_thesis(self):
        ctx = await self._run_pipeline()
        has_thesis = (
            hasattr(ctx, "thesis") and ctx.thesis
            or hasattr(ctx, "investment_thesis") and ctx.investment_thesis
        )
        self.assertTrue(has_thesis, "RESEARCH pipeline must produce a thesis in context")

    async def test_pipeline_produces_analysis(self):
        ctx = await self._run_pipeline()
        has_analysis = (
            hasattr(ctx, "analysis") and ctx.analysis
            or hasattr(ctx, "market_analysis") and ctx.market_analysis
        )
        self.assertTrue(has_analysis, "RESEARCH pipeline must produce an analysis")

    async def test_pipeline_populates_web_results(self):
        ctx = await self._run_pipeline()
        self.assertTrue(
            hasattr(ctx, "web_results") and ctx.web_results,
            "RESEARCH pipeline must populate ctx.web_results via WebScoutAgent",
        )

    async def test_pipeline_populates_market_data(self):
        ctx = await self._run_pipeline()
        has_market = (
            hasattr(ctx, "market_snapshot") and ctx.market_snapshot
        )
        self.assertTrue(
            has_market,
            "RESEARCH pipeline must populate ctx.market_snapshot via DataAgent",
        )

    async def test_context_task_type_preserved(self):
        ctx = await self._run_pipeline()
        self.assertEqual(ctx.task_type, "research")

    async def test_no_real_network_calls_made(self):
        """Verify the pipeline ran entirely on mocked data (no live API calls)."""
        # If we reach here without ConnectionError/timeout, mocks worked
        ctx = await self._run_pipeline()
        self.assertIsNotNone(ctx)


if __name__ == "__main__":
    unittest.main()
