"""SecurityAgent — Valida que el código no tenga vulnerabilidades críticas."""
from __future__ import annotations
from core.base_agent import BaseAgent
from core.context import AgentContext

# Patrones de seguridad que se buscan en el código generado por el LLM.
# Cada entrada es (patron_a_buscar, descripcion_del_riesgo).
# La búsqueda es case-insensitive (ver SecurityAgent.run).
#
# GRUPOS:
#   1. Ejecución arbitraria de código
#   2. Secrets hardcodeados
#   3. Exfiltración de secrets del sistema (ataque a través de código LLM-generado)
#   4. Comunicaciones de red no autorizadas

SECURITY_PATTERNS = [
    # --- Ejecución arbitraria ---
    ('eval(',          'Uso de eval() — riesgo de ejecución de código arbitrario'),
    ('exec(',          'Uso de exec() — riesgo de ejecución de código arbitrario'),
    ('os.system(',     'Uso de os.system() — usar subprocess con lista de args'),
    ('shell=True',     'subprocess con shell=True — riesgo de inyección de comandos'),
    ('subprocess.popen(', 'subprocess.Popen directo — verificar que no use shell=True'),
    ('pickle.loads',   'Deserialización insegura con pickle'),

    # --- Secrets hardcodeados ---
    ('SECRET',         'Posible secret hardcodeado'),
    ('PASSWORD',       'Posible password hardcodeado'),
    ('API_KEY',        'Posible API key hardcodeada'),

    # --- Exfiltración de secrets del sistema (Ataque 1: código LLM como intermediario) ---
    # El sandbox bloquea comandos peligrosos a nivel shell, pero no puede ver
    # la semántica del código Python que el LLM genera. Estos patrones detectan
    # intentos de leer credenciales del host a través del código generado.
    ('open(".env"',    'Intento de leer archivo .env — posible exfiltración de credenciales'),
    ("open('.env'",    'Intento de leer archivo .env — posible exfiltración de credenciales'),
    ('os.environ',     'Acceso a variables de entorno — puede exponer API keys y tokens'),
    ('load_dotenv',    'Carga programmática de .env — revisar uso de credenciales'),
    ('dotenv',         'Uso de python-dotenv — revisar que no exponga secrets'),

    # --- Comunicaciones de red no autorizadas ---
    # El código LLM-generado podría exfiltrar datos a un servidor externo.
    ('requests.post(', 'HTTP POST en código generado — verificar destino y payload'),
    ('http.client',    'Uso directo de http.client — verificar que no exfiltre datos'),
    ('urllib.request', 'Uso de urllib.request — verificar destino de la petición'),
    ('socket.',        'Uso de sockets raw — posible canal de exfiltración'),
]


class SecurityAgent(BaseAgent):
    name = "SecurityAgent"
    description = "Audita el código generado en busca de vulnerabilidades de seguridad."

    async def run(self, context: AgentContext) -> AgentContext:
        generated = context.get_data('generated_files') or {}
        security_report = []

        for file_path, code in generated.items():
            if not isinstance(code, str):
                continue
            file_issues = []
            for pattern, description in SECURITY_PATTERNS:
                if pattern.upper() in code.upper():
                    file_issues.append(f"  ⚠ {pattern}: {description}")

            if file_issues:
                security_report.append(f"{file_path}:")
                security_report.extend(file_issues)

        context.set_data('security_report', security_report)

        if security_report:
            self.log(
                context,
                f"⚠ Advertencias de seguridad encontradas en {len([l for l in security_report if l.startswith('  ')])} patrón(es):"
            )
            for line in security_report:
                self.log(context, line)
            self.log(
                context,
                "SecurityAgent reporta advertencias pero NO bloquea la ejecución. "
                "Revisa el security_report antes de hacer deploy."
            )
        else:
            self.log(context, "✅ Sin vulnerabilidades críticas detectadas")

        return context
