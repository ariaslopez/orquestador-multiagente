"""
AnalystAgent v2 — Análisis multidimensional con salida garantizada.

Responsabilidades:
  1. Consumir web_results de WebScoutAgent (campo 'description', no 'body')
  2. Incorporar market_data si el pipeline es TRADING o ANALYTICS
  3. Usar sequential_thinking.think() para razonar antes de generar
     el análisis en queries complejas o ambiguas
  4. Producir ctx.data['analysis'] estructurado en secciones fijas
     que ThesisAgent puede consumir de forma predecible
  5. Persistir el output en 'analystagent_output' para memoria episódica

Inputs desde ctx.data:
  web_results   : List[{title, url, description, published}]  (WebScoutAgent)
  web_queries   : List[str]   — queries ejecutadas (para contexto)
  web_provider  : str         — fuente de datos (para calidad del análisis)
  market_data   : dict        — opcional, TRADING/ANALYTICS pipeline
  memory_context: list        — inyectado por BaseAgent._before_run()

Outputs en ctx.data:
  analysis            : str   — análisis estructurado en 5 secciones
  analysis_sections   : dict  — análisis parseado por sección
  analysis_source_count: int  — número de fuentes usadas
  analysis_confidence : str   — 'alta' | 'media' | 'baja'
  analystagent_output : str   — clave estandarizada para BaseAgent._after_run()

Consumidores:
  ThesisAgent lee ctx.data['analysis'] como string estructurado.
  Otros agentes pueden usar ctx.data['analysis_sections'] para acceso
  por sección sin parsear el string completo.
"""
from __future__ import annotations

import logging
import re
from typing import Dict, List, Optional

from core.base_agent import BaseAgent
from core.context import AgentContext

logger = logging.getLogger(__name__)

# Número máximo de resultados web a incluir en el prompt
MAX_WEB_RESULTS_IN_PROMPT = 10

# Secciones obligatorias del análisis (ThesisAgent las espera)
ANALYSIS_SECTIONS = [
    "SITUACION ACTUAL",
    "FACTORES ALCISTAS",
    "FACTORES BAJISTAS",
    "METRICAS CLAVE",
    "CONTEXTO DE MERCADO",
]


class AnalystAgent(BaseAgent):
    """
    Analiza datos web, de mercado y de memoria para extraer insights
    estructurados que ThesisAgent pueda consumir de forma predecible.
    """

    name        = "AnalystAgent"
    description = (
        "Analiza datos web y de mercado para generar insights estructurados. "
        "Usa sequential_thinking para razonar en profundidad sobre topics complejos. "
        "Produce análisis en 5 secciones fijas compatibles con ThesisAgent."
    )

    # ------------------------------------------------------------------
    # Punto de entrada principal
    # ------------------------------------------------------------------

    async def run(self, ctx: AgentContext) -> AgentContext:
        topic = ctx.user_input.strip()
        self.log(ctx, f"🔎 Analizando: «{topic[:80]}»")

        # 1. Recolectar inputs del contexto
        web_results:    List[Dict] = ctx.get_data("web_results", [])
        web_queries:    List[str]  = ctx.get_data("web_queries", [topic])
        web_provider:   str        = ctx.get_data("web_provider", "unknown")
        market_data:    Dict       = ctx.get_data("market_data", {})
        memory_context: List       = ctx.get_data("memory_context", [])

        if not web_results and not market_data:
            self.log(ctx, "⚠ Sin datos de entrada — análisis degradado")
            analysis = self._fallback_analysis(topic)
            self._write_outputs(ctx, analysis, 0, "baja")
            return ctx

        # 2. Obtener marco de razonamiento con sequential_thinking
        reasoning_frame = await self._get_reasoning_frame(ctx, topic, web_results)

        # 3. Construir el bloque de datos para el prompt
        data_block   = self._build_data_block(web_results, web_queries, web_provider)
        market_block = self._build_market_block(market_data)
        memory_block = self._build_memory_block(memory_context)

        # 4. Llamar al LLM para generar el análisis estructurado
        self.log(ctx, f"🧠 Generando análisis ({len(web_results)} fuentes web, mercado={'sí' if market_data else 'no'})")
        analysis = await self._generate_analysis(
            ctx, topic, data_block, market_block, memory_block, reasoning_frame
        )

        # 5. Validar que el análisis tiene todas las secciones obligatorias
        analysis = self._ensure_sections(analysis, topic)

        # 6. Parsear secciones para acceso rápido por otros agentes
        sections = self._parse_sections(analysis)

        # 7. Calcular confianza basada en calidad de los datos
        confidence = self._estimate_confidence(web_results, market_data, web_provider)

        # 8. Escribir outputs
        self._write_outputs(ctx, analysis, len(web_results), confidence, sections)
        self.log(ctx, f"✅ Análisis completado (confianza={confidence}, fuentes={len(web_results)})")
        return ctx

    # ------------------------------------------------------------------
    # Razonamiento previo con sequential_thinking
    # ------------------------------------------------------------------

    async def _get_reasoning_frame(
        self,
        ctx: AgentContext,
        topic: str,
        web_results: List[Dict],
    ) -> str:
        """
        Usa sequential_thinking.think() para generar un marco de razonamiento
        antes del análisis. Sólo se activa si hay suficientes datos y el MCP
        está disponible. Es opcional: si falla, el análisis continúa igual.
        """
        if not ctx.is_mcp_available("sequential_thinking"):
            return ""
        if len(web_results) < 3:
            return ""  # insuficiente evidencia para razonar en profundidad

        try:
            result = await ctx.mcp_call(
                "sequential_thinking",
                "think",
                {
                    "problem": (
                        f"Analizar: {topic}. "
                        f"Tengo {len(web_results)} fuentes de información. "
                        "Identifica los 3 factores más importantes a considerar "
                        "y posibles sesgos en los datos."
                    ),
                    "steps": 4,
                    "depth": "normal",
                },
            )
            conclusion = result.get("conclusion", "")
            chain      = result.get("thinking_chain", [])
            if conclusion:
                self.log(ctx, f"💡 Marco de razonamiento: {conclusion[:120]}...")
                steps_text = "\n".join(
                    f"Paso {s.get('step', i+1)}: {s.get('reasoning', '')}"
                    for i, s in enumerate(chain[:3])
                )
                return f"MARCO DE RAZONAMIENTO PREVIO:\n{steps_text}\nConclusión: {conclusion}"
        except Exception as exc:
            logger.debug("[AnalystAgent] sequential_thinking.think falló: %s", exc)
        return ""

    # ------------------------------------------------------------------
    # Construcción de bloques de datos para el prompt
    # ------------------------------------------------------------------

    def _build_data_block(
        self,
        web_results: List[Dict],
        web_queries: List[str],
        provider: str,
    ) -> str:
        if not web_results:
            return "Sin resultados web disponibles."

        lines = [
            f"Fuente: {provider} | Queries ejecutadas: {', '.join(web_queries[:3])}",
            "",
        ]
        for i, r in enumerate(web_results[:MAX_WEB_RESULTS_IN_PROMPT], 1):
            title       = r.get("title", "Sin título")
            description = r.get("description", r.get("body", ""))  # compat. v1/v2
            url         = r.get("url", r.get("href", ""))
            published   = r.get("published", "")
            date_str    = f" [{published}]" if published else ""
            lines.append(f"[{i}] {title}{date_str}")
            lines.append(f"    {description[:280]}")
            if url:
                lines.append(f"    Fuente: {url}")
            lines.append("")
        return "\n".join(lines)

    def _build_market_block(self, market_data: Dict) -> str:
        if not market_data:
            return ""
        price     = market_data.get("price_usd", "N/A")
        change    = market_data.get("change_24h", "N/A")
        change_7d = market_data.get("change_7d", "N/A")
        mcap      = market_data.get("market_cap", "N/A")
        volume    = market_data.get("volume_24h", "N/A")
        symbol    = market_data.get("symbol", "").upper()
        extra = []
        for k, v in market_data.items():
            if k not in ("price_usd","change_24h","change_7d","market_cap","volume_24h","symbol"):
                extra.append(f"  {k}: {v}")
        block = (
            f"\n--- DATOS DE MERCADO EN TIEMPO REAL ({symbol}) ---\n"
            f"  Precio:     ${price}\n"
            f"  Cambio 24h: {change}%\n"
            f"  Cambio 7d:  {change_7d}%\n"
            f"  Market Cap: ${mcap}\n"
            f"  Volumen 24h:${volume}\n"
        )
        if extra:
            block += "\n".join(extra) + "\n"
        return block

    def _build_memory_block(self, memory_context: List) -> str:
        if not memory_context:
            return ""
        relevant = [
            m for m in memory_context
            if m.get("agent") in ("WebScoutAgent", "AnalystAgent")
        ]
        if not relevant:
            return ""
        lines = ["\n--- CONTEXTO DE SESIONES ANTERIORES ---"]
        for m in relevant[:2]:  # máximo 2 memorias para no inflar el prompt
            agent   = m.get("agent", "?")
            content = str(m.get("memory", ""))[:300]
            lines.append(f"[{agent}] {content}")
        return "\n".join(lines) + "\n"

    # ------------------------------------------------------------------
    # Generación del análisis vía LLM
    # ------------------------------------------------------------------

    async def _generate_analysis(
        self,
        ctx: AgentContext,
        topic: str,
        data_block: str,
        market_block: str,
        memory_block: str,
        reasoning_frame: str,
    ) -> str:
        reasoning_section = (
            f"\n{reasoning_frame}\n" if reasoning_frame else ""
        )
        prompt = f"""Eres un analista senior especializado en mercados financieros, tecnología y criptoactivos.
Analiza los siguientes datos sobre el tema: {topic}
{reasoning_section}
--- DATOS WEB ---
{data_block}
{market_block}{memory_block}
---

Genera un análisis estrictamente estructurado con EXACTAMENTE estas 5 secciones.
Cada sección debe empezar con el encabezado en mayúsculas seguido de dos puntos.
Basa TODO en los datos proporcionados. Sin opiniones, solo análisis con evidencia.

## 1. SITUACION ACTUAL:
(Estado presente del tema con datos concretos de las fuentes. Mínimo 3 puntos.)

## 2. FACTORES ALCISTAS:
(Argumentos positivos, tendencias favorables, catalizadores con evidencia de las fuentes.)

## 3. FACTORES BAJISTAS:
(Riesgos, tendencias negativas, argumentos contrarios con evidencia de las fuentes.)

## 4. METRICAS CLAVE:
(Números, porcentajes, comparativas. Formato tabla si es posible.)

## 5. CONTEXTO DE MERCADO:
(Macro, sector, correlaciones, benchmark. Basado en los datos disponibles.)"""

        return await self.llm(
            ctx,
            prompt,
            system=(
                "Eres un analista institucional. Respondes en español. "
                "Siempre mantienes la estructura de 5 secciones solicitada. "
                "Cada sección tiene mínimo 2 puntos con evidencia citada."
            ),
            temperature=0.2,
            max_tokens=3000,
        )

    # ------------------------------------------------------------------
    # Post-procesado
    # ------------------------------------------------------------------

    def _ensure_sections(self, analysis: str, topic: str) -> str:
        """
        Garantiza que el texto de salida contiene todas las secciones
        obligatorias. Si falta alguna, añade un placeholder para que
        ThesisAgent no rompa al parsear.
        """
        for section in ANALYSIS_SECTIONS:
            if section not in analysis.upper():
                analysis += f"\n\n## {section}:\n(Datos insuficientes para esta sección.)"
        return analysis

    def _parse_sections(self, analysis: str) -> Dict[str, str]:
        """
        Parsea el análisis en un dict {nombre_seccion: contenido}.
        Permite que otros agentes accedan a secciones individuales
        sin necesidad de manipular el string completo.
        """
        sections: Dict[str, str] = {}
        pattern = re.compile(
            r"##\s*\d+\.?\s*([A-ZÁÉÍÓÚ\s]+):?",
            re.IGNORECASE,
        )
        parts = pattern.split(analysis)
        # parts alterna entre separadores y contenidos
        for i in range(1, len(parts) - 1, 2):
            key     = parts[i].strip().upper()
            content = parts[i + 1].strip() if i + 1 < len(parts) else ""
            sections[key] = content
        return sections

    def _estimate_confidence(self, web_results, market_data, provider) -> str:
        score = 0
        if len(web_results) >= 7:    score += 2
        elif len(web_results) >= 3:  score += 1
        if market_data:              score += 2
        if provider == "brave":      score += 1
        if provider in ("deepwiki", "duckduckgo"): score += 0
        if score >= 4:   return "alta"
        if score >= 2:   return "media"
        return "baja"

    def _fallback_analysis(self, topic: str) -> str:
        return (
            f"## 1. SITUACION ACTUAL:\n"
            f"No se obtuvieron datos externos para analizar: {topic}.\n\n"
            f"## 2. FACTORES ALCISTAS:\n(Sin datos disponibles.)\n\n"
            f"## 3. FACTORES BAJISTAS:\n(Sin datos disponibles.)\n\n"
            f"## 4. METRICAS CLAVE:\n(Sin datos disponibles.)\n\n"
            f"## 5. CONTEXTO DE MERCADO:\n(Sin datos disponibles.)"
        )

    # ------------------------------------------------------------------
    # Escritura de outputs
    # ------------------------------------------------------------------

    def _write_outputs(
        self,
        ctx: AgentContext,
        analysis: str,
        source_count: int,
        confidence: str,
        sections: Optional[Dict] = None,
    ) -> None:
        ctx.set_data("analysis",             analysis)
        ctx.set_data("analysis_sections",    sections or {})
        ctx.set_data("analysis_source_count", source_count)
        ctx.set_data("analysis_confidence",  confidence)
        # Clave estandarizada para BaseAgent._after_run() → memoria episódica
        summary = analysis[:500]
        ctx.set_data("analystagent_output", summary)
