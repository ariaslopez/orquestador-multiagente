"""
ThesisAgent v2 — Síntesis institucional con calidad adaptativa.

Responsabilidades:
  1. Consumir ctx.data['analysis'] y ctx.data['analysis_sections']
     producidos por AnalystAgent v2 (5 secciones garantizadas)
  2. Incorporar ctx.data['web_sources'] como referencias citables
  3. Ajustar tono y profundidad según ctx.data['analysis_confidence']
     (alta → tesis completa; media → nota con advertencias; baja → resumen de limitaciones)
  4. Opcional: usar sequential_thinking.validate_plan() para auto-revisar
     la tesis generada antes de entregarla (si confidence >= 'media')
  5. Persistir output en 'thesisagent_output' para memoria episódica

Inputs desde ctx.data:
  analysis             : str   — análisis estructurado (AnalystAgent)
  analysis_sections    : dict  — análisis por sección (AnalystAgent)
  analysis_confidence  : str   — 'alta' | 'media' | 'baja' (AnalystAgent)
  analysis_source_count: int   — número de fuentes usadas (AnalystAgent)
  web_sources          : list  — URLs reales (WebScoutAgent)
  web_provider         : str   — fuente de datos (WebScoutAgent)

Outputs:
  ctx.data['thesis']          : str  — tesis completa en Markdown
  ctx.data['thesis_quality']  : str  — 'completa' | 'parcial' | 'limitada'
  ctx.data['thesis_sources']  : list — URLs citadas en la tesis
  ctx.data['thesisagent_output']: str — para BaseAgent._after_run()
  ctx.final_output            : str  — entrega al usuario
  ctx.pipeline_name           : str  — 'RESEARCH'
"""
from __future__ import annotations

import logging
from datetime import date
from typing import Dict, List, Optional

from core.base_agent import BaseAgent
from core.context import AgentContext

logger = logging.getLogger(__name__)

# Mapa de confianza → parámetros de generación
_CONFIDENCE_CONFIG = {
    "alta":  {"mode": "completa",  "temperature": 0.25, "max_tokens": 4000, "validate": True},
    "media": {"mode": "parcial",   "temperature": 0.30, "max_tokens": 2500, "validate": True},
    "baja":  {"mode": "limitada",  "temperature": 0.35, "max_tokens": 1500, "validate": False},
}
_DEFAULT_CONFIG = _CONFIDENCE_CONFIG["media"]

# Máximo de URLs a incluir como referencias en la tesis
MAX_SOURCES_IN_THESIS = 8


class ThesisAgent(BaseAgent):
    """
    Sintetiza el análisis de AnalystAgent en una tesis de investigación
    institucional. Ajusta profundidad, tono y longitud según la confianza
    del análisis subyacente. Incluye validación automática con
    sequential_thinking cuando los datos lo justifican.
    """

    name        = "ThesisAgent"
    description = (
        "Genera una tesis de investigación institucional en Markdown. "
        "Ajusta profundidad según confianza del análisis (alta/media/baja). "
        "Incluye fuentes citadas y auto-validación con sequential_thinking."
    )

    # ------------------------------------------------------------------
    # Punto de entrada principal
    # ------------------------------------------------------------------

    async def run(self, ctx: AgentContext) -> AgentContext:
        topic = ctx.user_input.strip()
        self.log(ctx, f"📝 Generando tesis: «{topic[:80]}»")

        # 1. Leer inputs del pipeline
        analysis:        str  = ctx.get_data("analysis", "")
        analysis_sections: Dict = ctx.get_data("analysis_sections", {})
        confidence:      str  = ctx.get_data("analysis_confidence", "media")
        source_count:    int  = ctx.get_data("analysis_source_count", 0)
        web_sources:     List = ctx.get_data("web_sources", [])
        web_provider:    str  = ctx.get_data("web_provider", "unknown")

        # Guardar pipeline_name desde el contexto o inferirlo
        ctx.pipeline_name = ctx.pipeline_name or "RESEARCH"

        # 2. Guardia: sin análisis no hay tesis posible
        if not analysis:
            self.log(ctx, "⚠ Sin análisis previo — tesis no generada")
            fallback = self._fallback_output(topic)
            self._write_outputs(ctx, fallback, "limitada", [])
            return ctx

        # 3. Seleccionar configuración según confianza
        cfg = _CONFIDENCE_CONFIG.get(confidence, _DEFAULT_CONFIG)
        self.log(ctx, f"📊 Confianza: {confidence} → modo {cfg['mode']} ({source_count} fuentes, provider={web_provider})")

        # 4. Seleccionar y formatear fuentes para citar
        cited_sources = self._select_sources(web_sources)

        # 5. Generar la tesis vía LLM
        today    = date.today().isoformat()
        thesis   = await self._generate_thesis(
            ctx, topic, analysis, cited_sources, confidence, today, cfg
        )

        # 6. Auto-validación con sequential_thinking (si aplica)
        if cfg["validate"] and ctx.is_mcp_available("sequential_thinking"):
            thesis = await self._validate_and_refine(ctx, thesis, topic)

        # 7. Añadir bloque de referencias al final
        thesis = self._append_references(thesis, cited_sources, today, web_provider)

        # 8. Escribir outputs
        self._write_outputs(ctx, thesis, cfg["mode"], cited_sources)
        self.log(ctx, f"✅ Tesis generada (modo={cfg['mode']}, {len(thesis)} chars, {len(cited_sources)} refs)")
        return ctx

    # ------------------------------------------------------------------
    # Generación de la tesis
    # ------------------------------------------------------------------

    async def _generate_thesis(
        self,
        ctx: AgentContext,
        topic: str,
        analysis: str,
        sources: List[str],
        confidence: str,
        today: str,
        cfg: Dict,
    ) -> str:
        confidence_note = {
            "alta":  "",
            "media": "\n> ⚠️ **Nota:** Análisis basado en datos parciales. Interpretar con cautela.",
            "baja":  "\n> ❌ **Advertencia:** Datos insuficientes. Esta tesis tiene valor limitado.",
        }.get(confidence, "")

        # Sección de modo degradado para confianza baja
        mode_instructions = {
            "completa": (
                "Genera la tesis COMPLETA con todas las secciones en profundidad. "
                "Incluye datos numéricos, comparativas y contexto macro."
            ),
            "parcial": (
                "Genera la tesis con las secciones principales. "
                "Indica explícitamente cuándo los datos son insuficientes para una conclusión sólida."
            ),
            "limitada": (
                "Los datos son insuficientes para una tesis completa. "
                "Genera un resumen breve con los pocos datos disponibles y "
                "una sección destacada de LIMITACIONES DEL ANÁLISIS."
            ),
        }[cfg["mode"]]

        prompt = f"""Eres un analista de investigación institucional. No das recomendaciones de compra/venta.
Basado en el siguiente análisis, genera una tesis de investigación.

TEMA: {topic}
FECHA: {today}
CALIDAD DE DATOS: {confidence.upper()}

INSTRUCCIONES: {mode_instructions}

ANÁLISIS BASE:
{analysis}

---
Estructura exacta de la tesis (usa estos encabezados literalmente):

# TESIS: {{Título descriptivo del tema}}
**Fecha:** {today} | **Calidad de datos:** {confidence.upper()} | **Fuentes:** {len(sources)}
{confidence_note}

## Resumen Ejecutivo
(3-4 oraciones con la tesis central. Qué, por qué importa, y cuál es el punto de vista analítico.)

## Bull Case
(Mínimo 3 argumentos alcistas con datos concretos del análisis. Formato de lista.)

## Bear Case
(Mínimo 3 riesgos o argumentos bajistas con evidencia. Formato de lista.)

## Métricas Clave
(Tabla Markdown con los números más relevantes del análisis. Mínimo 3 filas.)

## Riesgos Principales
(Lista ordenada por impacto potencial. Mínimo 3 riesgos.)

## Conclusión del Análisis
(Síntesis objetiva de 2-3 párrafos. Sin recomendación de acción.)

---
*Este documento es solo para fines informativos y no constituye asesoramiento financiero.*"""

        return await self.llm(
            ctx,
            prompt,
            system=(
                "Eres un analista institucional senior. Respondes en español. "
                "Mantienes la estructura solicitada exactamente. "
                "Usas lenguaje técnico pero claro. "
                "Jamas haces recomendaciones de compra/venta."
            ),
            temperature=cfg["temperature"],
            max_tokens=cfg["max_tokens"],
        )

    # ------------------------------------------------------------------
    # Validación con sequential_thinking
    # ------------------------------------------------------------------

    async def _validate_and_refine(
        self,
        ctx: AgentContext,
        thesis: str,
        topic: str,
    ) -> str:
        """
        Usa sequential_thinking.validate_plan() para detectar inconsistencias
        en la tesis: argumentos contradictorios, secciones débiles o sesgos.
        Si hay issues críticos, los añade como nota al final de la tesis.
        No regenera la tesis completa para mantener latencia baja.
        """
        try:
            validation = await ctx.mcp_call(
                "sequential_thinking",
                "validate_plan",
                {"plan_text": f"Tesis sobre: {topic}\n\n{thesis[:1500]}"},
            )
            issues      = validation.get("issues", [])
            suggestions = validation.get("suggestions", [])
            is_valid    = validation.get("valid", True)

            if not is_valid and issues:
                issues_md = "\n".join(f"- {i}" for i in issues[:3])
                suggestions_md = "\n".join(f"- {s}" for s in suggestions[:2])
                note = (
                    f"\n\n---\n"
                    f"## Notas de Revisión Automática\n"
                    f"**Observaciones detectadas:**\n{issues_md}\n"
                )
                if suggestions_md:
                    note += f"**Sugerencias:**\n{suggestions_md}\n"
                self.log(ctx, f"🔍 Validación: {len(issues)} observaciones encontradas")
                return thesis + note

            self.log(ctx, "✅ Validación: tesis consistente")
        except Exception as exc:
            logger.debug("[ThesisAgent] validate_plan falló: %s", exc)
        return thesis

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _select_sources(self, web_sources: List[str]) -> List[str]:
        """Selecciona hasta MAX_SOURCES_IN_THESIS URLs únicas y limpias."""
        seen, clean = set(), []
        for url in web_sources:
            url = url.strip()
            if url and url not in seen and url.startswith("http"):
                seen.add(url)
                clean.append(url)
                if len(clean) >= MAX_SOURCES_IN_THESIS:
                    break
        return clean

    def _append_references(
        self,
        thesis: str,
        sources: List[str],
        today: str,
        provider: str,
    ) -> str:
        """Añade un bloque de Referencias al final de la tesis."""
        if not sources:
            return thesis
        refs = "\n".join(f"{i+1}. {url}" for i, url in enumerate(sources))
        return (
            thesis
            + f"\n\n---\n## Referencias\n"
            + f"*Fuente: {provider} | Consultado: {today}*\n\n"
            + refs
        )

    def _fallback_output(self, topic: str) -> str:
        today = date.today().isoformat()
        return (
            f"# TESIS: {topic}\n"
            f"**Fecha:** {today} | **Calidad de datos:** SIN DATOS\n\n"
            f"> ❌ **Error:** AnalystAgent no produjo análisis. "
            f"Verifica que WebScoutAgent obtuvo resultados.\n\n"
            f"## Limitaciones del Análisis\n"
            f"No se pudieron obtener datos externos para: {topic}.\n\n"
            f"---\n*Este documento no constituye asesoramiento financiero.*"
        )

    def _write_outputs(
        self,
        ctx: AgentContext,
        thesis: str,
        quality: str,
        sources: List[str],
    ) -> None:
        ctx.set_data("thesis",           thesis)
        ctx.set_data("thesis_quality",   quality)
        ctx.set_data("thesis_sources",   sources)
        # Clave estandarizada para BaseAgent._after_run() → memoria episódica
        ctx.set_data("thesisagent_output", thesis[:500])
        ctx.final_output  = thesis
        ctx.pipeline_name = ctx.pipeline_name or "RESEARCH"
