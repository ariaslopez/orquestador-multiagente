"""AnalystAgent — Analiza los datos recopilados y extrae insights."""
from __future__ import annotations
from core.base_agent import BaseAgent
from core.context import AgentContext


class AnalystAgent(BaseAgent):
    name = "AnalystAgent"
    description = "Analiza datos web y locales para extraer patrones e insights clave."

    async def run(self, context: AgentContext) -> AgentContext:
        web_results = context.get_data('web_results', [])
        market_data = context.get_data('market_data', {})

        if not web_results and not market_data:
            self.log(context, "Sin datos para analizar")
            return context

        raw_data = "\n\n".join(
            f"[{r['title']}]\n{r['body']}" for r in web_results[:8]
        )

        # Agregar datos de mercado si existen
        market_summary = ""
        if market_data:
            price = market_data.get('price_usd', 'N/A')
            change = market_data.get('change_24h', 'N/A')
            mcap = market_data.get('market_cap', 'N/A')
            market_summary = f"\n\nDATOS DE MERCADO EN TIEMPO REAL:\nPrecio: ${price} | Cambio 24h: {change}% | Market Cap: ${mcap}"

        self.log(context, "Analizando datos recopilados...")
        prompt = f"""Eres un analista senior especializado en mercados financieros y tecnologia.
Analiza los siguientes datos sobre: {context.user_input}

DATOS WEB:
{raw_data}{market_summary}

Genera un analisis estructurado con:
1. SITUACION ACTUAL (estado presente con datos concretos)
2. FACTORES ALCISTAS (argumentos positivos con evidencia)
3. FACTORES BAJISTAS (riesgos y argumentos negativos con evidencia)
4. METRICAS CLAVE (numeros, porcentajes, comparativas)
5. CONTEXTO DE MERCADO (macro y sector)

Basa TODO en los datos proporcionados. Sin opiniones, solo analisis con evidencia."""
        analysis = await self.llm(context, prompt, temperature=0.2)
        context.set_data('analysis', analysis)
        self.log(context, "Analisis completado")
        return context
