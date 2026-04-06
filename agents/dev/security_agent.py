"""SecurityAgent — Valida que el codigo no tenga vulnerabilidades criticas."""
from __future__ import annotations
from core.base_agent import BaseAgent
from core.context import AgentContext

SECURITY_PATTERNS = [
    ('eval(', 'Uso de eval() — riesgo de ejecucion de codigo arbitrario'),
    ('exec(', 'Uso de exec() — riesgo de ejecucion de codigo arbitrario'),
    ('os.system(', 'Uso de os.system() — usar subprocess con lista de args'),
    ('shell=True', 'subprocess con shell=True — riesgo de inyeccion de comandos'),
    ('pickle.loads', 'Deserializacion insegura con pickle'),
    ('SECRET', 'Posible secret hardcodeado'),
    ('PASSWORD', 'Posible password hardcodeado'),
    ('API_KEY', 'Posible API key hardcodeada'),
]


class SecurityAgent(BaseAgent):
    name = "SecurityAgent"
    description = "Audita el codigo generado en busca de vulnerabilidades de seguridad."

    async def run(self, context: AgentContext) -> AgentContext:
        generated = getattr(context, 'generated_files', {})
        security_report = []

        for file_path, code in generated.items():
            file_issues = []
            for pattern, description in SECURITY_PATTERNS:
                if pattern.upper() in code.upper():
                    file_issues.append(f"  ⚠ {pattern}: {description}")

            if file_issues:
                security_report.append(f"{file_path}:")
                security_report.extend(file_issues)

        context.security_report = security_report
        if security_report:
            self.log(context, f"⚠ Advertencias de seguridad encontradas en {len(security_report)} items")
            for line in security_report:
                self.log(context, line)
        else:
            self.log(context, "✅ Sin vulnerabilidades criticas detectadas")
        return context
