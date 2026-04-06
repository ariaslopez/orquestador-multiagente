"""ComplianceCheckerAgent — verifica compliance con GDPR, CCPA y términos de APIs."""
from __future__ import annotations
from core.base_agent import BaseAgent
from core.context import AgentContext


class ComplianceCheckerAgent(BaseAgent):
    name = "ComplianceCheckerAgent"
    description = "Verifica compliance con GDPR, CCPA, SOC2 y términos de servicio de APIs."

    async def run(self, context: AgentContext) -> AgentContext:
        threat_model = context.get_data('threat_model') or ''
        security_review = context.get_data('security_review') or ''
        self.log(context, "Verificando compliance regulatorio...")

        prompt = f"""Eres un compliance officer y DPO con experiencia en regulaciones de privacidad.

SISTEMA: {context.user_input}

MODELO DE AMENAZAS: {threat_model[:1000]}
REVISIÓN DE SEGURIDAD: {security_review[:1500]}

Genera el reporte de compliance y auditoría final:

## GDPR COMPLIANCE
| Artículo | Requisito | Estado | Gaps detectados |
|---------|-----------|--------|----------------|

## CCPA COMPLIANCE
| Requisito | Estado | Acción necesaria |
|-----------|--------|------------------|

## TÉRMINOS DE API
APIs usadas y posibles violaciones de ToS detectadas.

## MANEJO DE DATOS
- Datos personales recopilados
- Bases legales de procesamiento
- Retención y eliminación
- Transferencias internacionales

## GAPS CRÍTICOS
Incumplimientos que generan riesgo legal inmediato.

# REPORTE DE AUDITORÍA DE SEGURIDAD — FINAL

## SECURITY SCORE
| Dimensión | Score (0-10) | Justificación |
|-----------|-------------|---------------|
| Código | | |
| Arquitectura | | |
| Compliance | | |
| **TOTAL** | | |

## PLAN DE REMEDIACIÓN
| Prioridad | Acción | Responsable | Plazo |
|-----------|--------|------------|-------|
| CRÍTICA | | | |
| ALTA | | | |
| MEDIA | | | |"""

        result = await self.llm(context, prompt, temperature=0.15)
        context.final_output = result
        context.pipeline_name = "SECURITY_AUDIT"
        self.log(context, "Auditoría de seguridad completa — SECURITY_AUDIT pipeline completado")
        return context
