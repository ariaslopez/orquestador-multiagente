"""SecurityCodeReviewerAgent — revisión de código con OWASP Top 10."""
from __future__ import annotations
from core.base_agent import BaseAgent
from core.context import AgentContext


class SecurityCodeReviewerAgent(BaseAgent):
    name = "SecurityCodeReviewerAgent"
    description = "Revisa código buscando vulnerabilidades OWASP Top 10 y malas prácticas de seguridad."

    async def run(self, context: AgentContext) -> AgentContext:
        threat_model = context.get_data('threat_model') or ''
        file_content = context.get_data('file_content') or ''
        code_context = file_content or context.user_input
        self.log(context, "Revisando código con OWASP Top 10...")

        prompt = f"""Eres un security engineer especializado en code review y OWASP.

SISTEMA: {context.user_input}

MODELO DE AMENAZAS:
{threat_model[:1500]}

CÓDIGO A REVISAR:
{code_context[:2500]}

Revisa con OWASP Top 10:

## VULNERABILIDADES ENCONTRADAS
| ID | Vulnerabilidad OWASP | Ubicación | Severidad | CWE |
|----|---------------------|-----------|----------|-----|

## ANÁLISIS POR CATEGORÍA OWASP
- A01 Broken Access Control:
- A02 Cryptographic Failures:
- A03 Injection:
- A04 Insecure Design:
- A05 Security Misconfiguration:
- A06 Vulnerable Components:
- A07 Auth Failures:
- A08 Software Integrity Failures:
- A09 Logging Failures:
- A10 SSRF:

## CÓDIGO VULNERABLE (snippets)
Muestra el patrón problemático y la corrección propuesta.

## REMEDIACIONES PRIORITARIAS
| Vulnerabilidad | Fix recomendado | Esfuerzo | Urgencia |
|----------------|----------------|---------|----------|"""

        result = await self.llm(context, prompt, temperature=0.1)
        context.set_data('security_review', result)
        self.log(context, "Code review de seguridad completado")
        return context
