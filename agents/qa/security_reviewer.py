"""SecurityReviewerAgent — OWASP Top 10, secrets expuestos, injection vulnerabilities."""
from __future__ import annotations
from pathlib import Path
from core.base_agent import BaseAgent
from core.context import AgentContext


class SecurityReviewerAgent(BaseAgent):
    name = "SecurityReviewerAgent"
    description = "Revisa vulnerabilidades de seguridad: OWASP, secrets, injections, auth."

    async def run(self, context: AgentContext) -> AgentContext:
        code = self._load_code(context)
        bugs_found = context.get_data('bugs_found') or ''
        self.log(context, "Revision de seguridad OWASP...")

        prompt = f"""Eres un security engineer especializado en appsec y pen testing.

CODIGO:
{code[:3500]}

BUGS YA DETECTADOS (no repetir):
{bugs_found[:300]}

Realiza una revision de seguridad exhaustiva:

## OWASP TOP 10 — REVISADO
Para cada categoria, indica si aplica (VULNERABLE / SEGURO / N/A):
- A01 Broken Access Control
- A02 Cryptographic Failures
- A03 Injection (SQL, NoSQL, Command)
- A04 Insecure Design
- A05 Security Misconfiguration
- A06 Vulnerable Components
- A07 Auth Failures
- A08 Software Integrity Failures
- A09 Logging Failures
- A10 SSRF

## SECRETS / CREDENCIALES EXPUESTAS
- API keys, tokens, passwords hardcodeados
- Variables de entorno no validadas

## SUPERFICIES DE ATAQUE
- Endpoints sin autenticacion
- Inputs sin sanitizar
- Deserializacion insegura

## SEVERIDAD TOTAL: CRITICA / ALTA / MEDIA / BAJA
## CVES APLICABLES (si conoces alguno relevante)"""

        result = await self.llm(context, prompt, temperature=0.05)
        context.set_data('security_issues', result)
        self.log(context, "Revision de seguridad completada")
        return context

    def _load_code(self, context: AgentContext) -> str:
        input_file = getattr(context, 'input_file', None)
        input_repo = getattr(context, 'input_repo', None)
        if input_file and Path(input_file).exists():
            return Path(input_file).read_text(encoding='utf-8')
        if input_repo:
            return f"Repositorio: {input_repo}\n{context.user_input}"
        return context.user_input
