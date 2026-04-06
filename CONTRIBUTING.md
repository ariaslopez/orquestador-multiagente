# Guía de Contribución — CLAW Agent System

Gracias por tu interés en contribuir. Este documento define las convenciones
del proyecto para que cualquier cambio sea predecible, seguro y fácil de revisar.

---

## 🛠️ Stack de referencia

| Capa | Tecnología |
|------|------------|
| Backend / agentes | Python 3.11+ |
| Base de datos | Supabase (PostgreSQL) + SQLite local |
| Frontend | HTML + Tailwind + Jinja2 |
| LLM principal | Groq (llama-3.3-70b) |
| LLM fallback | Gemini 2.0 Flash |
| LLM offline | Ollama (opcional) |
| Deploy | Fly.io / Docker (pendiente) |
| CI | GitHub Actions (pytest en cada push a `main`) |

---

## 🌿 Ramas y flujo de trabajo

```
main         ← rama de producción, siempre verde
feature/*    ← nuevas funcionalidades
fix/*        ← correcciones de bugs
security/*   ← parches de seguridad (merge prioritario)
docs/*       ← solo documentación
```

**Reglas:**
- Nunca hacer push directo a `main` con cambios de código (sí a docs menores).
- Toda rama debe tener al menos un commit descriptivo antes de abrir PR.
- Los PRs deben pasar el CI (pytest) antes de hacer merge.

---

## 📝 Estilo de commits

Usamos [Conventional Commits](https://www.conventionalcommits.org/es/v1.0.0/):

```
<tipo>: <descripción concisa en inglés>

[cuerpo opcional: qué cambió y por qué]
[Fixes #issue]
```

| Tipo | Cuándo usarlo |
|------|----------------|
| `feat` | Nueva funcionalidad |
| `fix` | Corrección de bug |
| `security` | Parche de seguridad |
| `docs` | Solo documentación |
| `refactor` | Refactor sin cambio de comportamiento |
| `test` | Añadir o corregir tests |
| `chore` | Mantenimiento (deps, CI, config) |
| `perf` | Mejora de rendimiento |

**Ejemplos correctos:**
```
feat: add async retry logic to api_router
fix: handle None context in analyst_agent
security: replace shell=True with shlex.split in code_executor
docs: document offline vs cloud modes in README
```

---

## ✅ Checklist de PR

Antes de solicitar revisión, verifica:

- [ ] `python main.py --doctor` pasa sin errores críticos
- [ ] Los tests existentes siguen pasando (`pytest tests/ -v`)
- [ ] Si añadiste un agente nuevo, hay al menos un test unitario
- [ ] Si modificaste `config.yaml` o `requirements.txt`, lo mencionas en el PR
- [ ] No hay claves, tokens ni secrets en el código
- [ ] El ROADMAP.md está actualizado si completaste un ítem de deuda técnica
- [ ] Si el cambio afecta seguridad (sandbox, executor, filesystem), lo indicas explícitamente

---

## 🐍 Estándares de código Python

- **Python 3.11+** — usa type hints, f-strings, `pathlib.Path`.
- **Sin dependencias nuevas** si existe alternativa en stdlib o en el stack actual.
- **Manejo explícito de errores** — nunca `except Exception: pass` silencioso.
- **Variables descriptivas** — sin abreviaciones crípticas (`ctx` está bien, `x` no).
- **Comentarios** solo cuando el código no es autoexplicativo.
- **Async** — todos los métodos `run()` de agentes son `async def`.

### Agentes nuevos

Todo agente debe extender `BaseAgent` de `core/base_agent.py`:

```python
from core.base_agent import BaseAgent
from core.context import AgentContext

class MiNuevoAgent(BaseAgent):
    async def run(self, context: AgentContext) -> AgentContext:
        # 1. Leer del contexto lo que necesitas
        # 2. Llamar al LLM o tool correspondiente
        # 3. Escribir resultado de vuelta al contexto
        # 4. Retornar contexto
        return context
```

Registra el agente en `config.yaml` bajo el pipeline correspondiente.

---

## 🔐 Reglas de seguridad (obligatorias)

1. **Nunca usar `shell=True`** en `subprocess` — usar `shlex.split()` + `shell=False`.
2. **Nunca hardcodear credenciales** — todo va en `.env` (que está en `.gitignore`).
3. **Nunca modificar** `PROTECTED_PATHS` ni `BLOCKED_PATTERNS` en `security_sandbox.py` sin discusión previa.
4. **Ejecutar `run_secret_scanning`** antes de hacer push si tu cambio toca archivos de configuración.
5. **`GITHUB_CONFIRM_BEFORE_PUSH` debe permanecer `true`** en `.env.example` y en el `.env` generado por `setup.py`.

---

## 📚 Deuda técnica

- Si encuentras algo que no funciona bien pero no es urgente, ábrelo como issue o añádelo a la sección `Pendiente` de `ROADMAP.md`.
- No ignores deuda técnica silenciosamente — regístrala.
- Prioridad de resolución: **seguridad > bug > performance > features > docs**.

---

## 🧪 Tests

```bash
# Correr todos los tests
pytest tests/ -v

# Correr solo tests del core
pytest tests/test_core.py -v

# Correr con cobertura (requiere pytest-cov)
pytest tests/ --cov=. --cov-report=term-missing
```

Estructura esperada de tests:

```
tests/
├── test_core.py          # maestro, pipeline_router, context
├── test_agents.py        # agentes por pipeline
├── test_infrastructure.py # memory, sandbox, security
└── test_tools.py         # code_executor, file_ops, crypto_data
```

---

## 📦 Dependencias

- Agregar dependencias a `requirements.txt` con versión mínima (`>=`).
- **No agregar `asyncio`, `shutil`, `os`, `re` ni otros módulos stdlib** a `requirements.txt`.
- Si la dependencia es solo para modo offline, añadirla bajo el bloque `# Legacy (offline mode)`.
- Documentar la razón si la dependencia es grande (>50 MB instalada).

---

*Última actualización: v1.0.0*
