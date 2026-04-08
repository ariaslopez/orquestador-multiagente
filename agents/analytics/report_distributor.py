"""
ReportDistributorAgent v2 — Formatea y distribuye el reporte de analytics.

Estrategia:
  1. LLM genera el reporte ejecutivo estructurado (siempre)
  2. supabase_mcp disponible → persiste el reporte en tabla 'analytics_reports'
  3. slack MCP disponible   → envía resumen ejecutivo al canal configurado
     Fallback: reporte disponible solo en ctx.final_output

Inputs esperados en ctx:
  - ctx.data['insights']        : texto con insights del InsightGeneratorAgent
  - ctx.data['collected_data']  : datos crudos del DataCollectorAgent (opcional)
  - ctx.user_input              : solicitud original del usuario
  - ctx.data['slack_channel']   : canal Slack destino (default: '#analytics')

Outputs en ctx:
  - ctx.final_output            : reporte ejecutivo completo en Markdown
  - ctx.data['report_id']       : UUID del registro en Supabase (si se persistó)
  - ctx.data['slack_sent']      : bool
  - ctx.data['supabase_saved']  : bool
  - ctx.pipeline_name           : 'ANALYTICS'
"""
from __future__ import annotations
import json
import logging
from datetime import datetime, timezone
from core.base_agent import BaseAgent
from core.context import AgentContext

logger = logging.getLogger(__name__)


class ReportDistributorAgent(BaseAgent):
    name = "ReportDistributorAgent"
    description = (
        "Formatea insights en reportes ejecutivos y los distribuye "
        "vía Supabase (persistencia) y Slack (notificación)."
    )

    async def run(self, ctx: AgentContext) -> AgentContext:
        self.log(ctx, "[Distributor] Formateando reporte final de analytics...")

        insights: str = ctx.get_data("insights") or ""
        collected_data: str = ctx.get_data("collected_data") or ""

        # --- Paso 1: LLM genera el reporte ejecutivo estructurado ---
        prompt = f"""Eres un director de analytics redactando el reporte semanal para stakeholders.

SOLICITUD: {ctx.user_input}

INSIGHTS:
{insights[:3000]}

Genera el reporte ejecutivo final:

# REPORTE DE ANALYTICS

## RESUMEN EJECUTIVO
(4-5 frases con los hallazgos más críticos. Para C-level, sin jerga técnica.)

## DASHBOARD DE KPIs
| KPI | Valor Actual | Período Anterior | Variación | Estado |
|-----|-------------|-----------------|-----------|--------|

## INSIGHTS CLAVE
(Top 3, con impacto estimado en negocio)

## ACCIONES RECOMENDADAS
| Acción | Owner sugerido | Plazo | Impacto esperado |
|--------|---------------|-------|------------------|

## PRÓXIMO REPORTE
Fecha sugerida y métricas a monitorear hasta entonces."""

        report: str = await self.llm(ctx, prompt, temperature=0.2)
        ctx.final_output = report
        ctx.pipeline_name = "ANALYTICS"

        # Extraer resumen ejecutivo (primeras 4 líneas no vacías tras ## RESUMEN)
        executive_summary = self._extract_summary(report)

        # --- Paso 2: Persistir en Supabase ---
        supabase_saved = False
        report_id: str = ""

        if ctx.is_mcp_available("supabase_mcp"):
            try:
                timestamp = datetime.now(timezone.utc).isoformat()
                insert_result = await ctx.mcp_call(
                    "supabase_mcp",
                    "execute",
                    {
                        "sql": (
                            "INSERT INTO analytics_reports "
                            "(created_at, user_input, executive_summary, full_report, pipeline) "
                            "VALUES ($1, $2, $3, $4, $5) "
                            "RETURNING id"
                        ),
                        "params": [
                            timestamp,
                            ctx.user_input[:500],
                            executive_summary[:1000],
                            report[:8000],
                            "ANALYTICS",
                        ],
                    },
                )
                rows = insert_result.get("rows") or insert_result.get("data") or []
                if rows:
                    report_id = str(rows[0].get("id", ""))
                supabase_saved = True
                self.log(ctx, f"[Distributor] supabase_mcp: reporte persistido (id={report_id or 'N/A'})")
            except Exception as exc:
                logger.warning(
                    "[Distributor] supabase_mcp falló al guardar reporte: %s — reporte solo en ctx", exc
                )
        else:
            logger.debug("[Distributor] supabase_mcp no disponible — persistencia omitida")

        # --- Paso 3: Enviar notificación a Slack ---
        slack_sent = False
        slack_channel: str = (
            ctx.get_data("slack_channel")
            or getattr(ctx, "slack_channel", None)
            or "#analytics"
        )

        if ctx.is_mcp_available("slack"):
            try:
                # Construir mensaje plano y legible para Slack
                supabase_ref = f" | ID Supabase: `{report_id}`" if report_id else ""
                slack_message = (
                    f"*📊 Reporte de Analytics — CLAW*{supabase_ref}\n\n"
                    f"*Solicitud:* {ctx.user_input[:200]}\n\n"
                    f"*Resumen ejecutivo:*\n{executive_summary}\n\n"
                    f"_Reporte completo disponible en el sistema._"
                )

                await ctx.mcp_call(
                    "slack",
                    "slack_post_message",
                    {
                        "channel": slack_channel,
                        "text": slack_message,
                    },
                )
                slack_sent = True
                self.log(ctx, f"[Distributor] slack: mensaje enviado a {slack_channel}")
            except Exception as exc:
                logger.warning(
                    "[Distributor] slack falló al enviar a %s: %s — reporte solo en ctx",
                    slack_channel,
                    exc,
                )
        else:
            logger.debug("[Distributor] slack MCP no disponible — envío omitido")

        ctx.set_data("report_id", report_id)
        ctx.set_data("supabase_saved", supabase_saved)
        ctx.set_data("slack_sent", slack_sent)

        self.log(
            ctx,
            f"[Distributor] ✓ ANALYTICS pipeline completado "
            f"| supabase={'sí (id=' + report_id + ')' if supabase_saved else 'no'} "
            f"| slack={'sí (' + slack_channel + ')' if slack_sent else 'no'}",
        )
        return ctx

    def _extract_summary(self, report: str) -> str:
        """Extrae el bloque de Resumen Ejecutivo del reporte Markdown."""
        lines = report.splitlines()
        capturing = False
        summary_lines: list[str] = []
        for line in lines:
            if "RESUMEN EJECUTIVO" in line.upper():
                capturing = True
                continue
            if capturing:
                if line.startswith("##"):  # siguiente sección
                    break
                if line.strip():
                    summary_lines.append(line.strip())
                    if len(summary_lines) >= 5:
                        break
        return "\n".join(summary_lines) if summary_lines else report[:400]
