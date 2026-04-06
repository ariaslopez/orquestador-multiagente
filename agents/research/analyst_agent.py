"""AnalystAgent — Analiza los datos recopilados y extrae insights."""
from __future__ import annotations
from core.base_agent import BaseAgent
from core.context import AgentContext


class AnalystAgent(BaseAgent):
    name = "AnalystAgent"
    description = "Analiza datos web y locales para extraer patrones e insights clave."

    async def run(self, context: AgentContext) -> AgentContext:
        web_results = getattr(context, 'web_results', [])
        if not web_results:
            self.log(context, "Sin datos para analizar")
            return context

        raw_data = "\n\n".join(
            f"[{r['title']}]\n{r['body']}" for r in web_results[:8]
        )
        self.log(context, "Analizando datos recopilados...")
        prompt = f"""Eres un analista senior especializado en mercados financieros y tecnologia.
Analiza los siguientes datos sobre: {context.user_input}

DATOS:
{raw_data}

Genera un analisis estructurado con:
1. SITUACION ACTUAL (estado presente con datos concretos)
2. FACTORES ALCISTAS (argumentos positivos con evidencia)
3. FACTORES BAJISTAS (riesgos y argumentos negativos con evidencia)
4. METRICAS CLAVE (numeros, porcentajes, comparativas)
5. CONTEXTO DE MERCADO (macro y sector)

Basa TODO en los datos proporcionados. Sin opiniones, solo analisis con evidencia."""
        analysis = await self.llm(context, prompt, temperature=0.2)
        context.analysis = analysis
        self.log(context, "Analisis completado")
        return context
