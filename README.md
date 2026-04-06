# 🤖 CLAW Agent System — Orquestador Multi-Agente

**Versión:** 1.0.0 · **Estado:** Producción supervisada · **Pipelines:** 7 activos → 12 planificados

Sistema de inteligencia artificial multi-agente diseñado para automatizar trabajo de desarrollo, investigación, contenido y análisis. Un Maestro central clasifica cada tarea y la delega al pipeline correcto. Los agentes colaboran en secuencia o en paralelo, compartiendo un contexto tipado.

> **Roadmap activo:** Ver `ROADMAP.md` para fases completadas y próximas.  
> **Mapa de agentes:** Ver `ARCHITECTURE.md` para el diseño completo de 70 agentes → 12 pipelines.

---

## 🧠 Arquitectura de alto nivel

```text
┌─────────────────────────────────────────────────────────┐
│                    MAESTRO (LLM)                        │
│  Clasifica tarea → keywords + LLM → selecciona pipeline │
└────────┬──────────┬──────────┬──────────┬──────────┬───┘
         │          │          │          │          │
    ┌────▼───┐ ┌────▼────┐ ┌──▼────┐ ┌──▼──┐ ┌────▼───┐
    │  DEV   │ │RESEARCH │ │CONTENT│ │ QA  │ │   ...  │
    │6 agts  │ │4 agts   │ │macro  │ │macro│ │ 7 total│
    │secuenc.│ │par+seq  │ │       │ │     │ │        │
    └────┬───┘ └────┬────┘ └───────┘ └─────┘ └────────┘
         └──────────┴──────────────────┐
                                       ▼
                    ┌─────────────────────────────┐
                    │      AgentContext tipado     │
                    │  Memoria · Logs · Seguridad  │
                    │   (SQLite + Supabase)        │
                    └─────────────────────────────┘
```

- `core/maestro.py` — Orquestador central: clasifica tarea y construye el pipeline.
- `core/pipeline_router.py` — Ejecutor: secuencial o `parallel_then_sequential`.
- `core/api_router.py` — Router de LLMs: Groq (principal) → Gemini (fallback) → Hyperspace (offline).
- `infrastructure/memory_manager.py` — Memoria: SQLite local + sync a Supabase.
- `infrastructure/security_sandbox.py` — Sandbox de filesystem y comandos con audit log.

---

## 🔀 Pipelines disponibles

| Pipeline | Flag | Descripción | Estado |
|----------|------|-------------|--------|
| **DEV** | `--type dev` | Genera proyectos completos: plan → código → review → seguridad → ejecución → git | ✅ Sub-pipeline (6 agentes) |
| **RESEARCH** | `--type research` | Tesis de inversión: web + datos mercado (paralelo) → análisis → tesis | ✅ Sub-pipeline (4 agentes) |
| **CONTENT** | `--type content` | Contenido crypto: hilos, posts, newsletters con personalidades LLM | ⚠️ Macro (Fase 8) |
| **OFFICE** | `--type office` | Analiza Excel, PDF, Word, CSV y genera reportes estructurados | ⚠️ Macro (Fase 8) |
| **QA** | `--type qa` | Auditoría de código: bugs, seguridad, performance, tests | ⚠️ Macro (Fase 8) |
| **TRADING** | `--type trading` | Analytics de bots: backtest, Sharpe, drawdown, recomendaciones | ⚠️ Macro (Fase 8) |
| **PM** | `--type pm` | Backlog, épicas, sprints y roadmap desde una descripción libre | ⚠️ Macro (Fase 8) |

**Próximos (Fase 8-9):** DESIGN, MARKETING, ANALYTICS, PRODUCT, SECURITY_AUDIT.

---

## 🌐 Modos de operación

### Modo Cloud-First (por defecto)

| Componente | Servicio | Costo |
|------------|----------|-------|
| LLM principal | Groq `llama-3.3-70b` | Gratis (con límites) |
| LLM fallback | Gemini 2.0 Flash | Gratis (con límites) |
| Memoria cloud | Supabase | Gratis (free tier) |
| Búsqueda web | DuckDuckGo | Gratis, sin API key |
| Datos crypto | CoinGecko + DeFiLlama | Gratis, sin API key |

```env
# .env mínimo
GROQ_API_KEY=tu_clave_groq       # Obligatorio
GEMINI_API_KEY=tu_clave          # Opcional (fallback)
SUPABASE_URL=...                 # Opcional (memoria cloud)
SUPABASE_KEY=...                 # Opcional (memoria cloud)
```

### Modo Offline (Ollama + ChromaDB)

Modelos locales, sin internet ni API keys. Privacidad total.

```env
HYPERSPACE_ENABLED=true
HYPERSPACE_BASE_URL=http://localhost:11434/v1
GROQ_API_KEY=   # Vacío para forzar fallback local
```

**Prerequisito:** `ollama pull llama3.1:8b`

> **Limitación:** Calidad inferior a modelos 70B. Los pipelines RESEARCH y TRADING requieren red para CoinGecko/DeFiLlama.

---

## 📁 Estructura del proyecto

```text
orquestador-multiagente/
├── core/
│   ├── base_agent.py          # Contrato base de todos los agentes
│   ├── context.py             # Estado compartido (AgentContext tipado)
│   ├── maestro.py             # Orquestador central
│   ├── api_router.py          # Router LLMs (Groq → Gemini → Hyperspace)
│   ├── pipeline.py            # Definición de pipeline lógico
│   └── pipeline_router.py     # Ejecutor secuencial / parallel+sequential
├── agents/
│   ├── dev/                   # 6 agentes: planner, coder, reviewer,
│   │                          #            security, executor, git
│   ├── research/              # 4 agentes: webscout, data, analyst, thesis
│   ├── content_agent.py       # Macro (→ sub-pipeline en Fase 8)
│   ├── office_agent.py        # Macro (→ sub-pipeline en Fase 8)
│   ├── qa_agent.py            # Macro (→ sub-pipeline en Fase 8)
│   ├── trading_agent.py       # Macro (→ sub-pipeline en Fase 8)
│   └── pm_agent.py            # Macro (→ sub-pipeline en Fase 8)
├── infrastructure/
│   ├── memory_manager.py      # SQLite + Supabase
│   ├── security_layer.py      # 5 capas de protección
│   ├── security_sandbox.py    # Sandbox filesystem/comandos
│   ├── audit_logger.py        # Logs estructurados
│   ├── state_manager.py       # Estado de sesión
│   └── output_manager.py      # Carpetas de salida
├── tools/
│   ├── web_search.py          # DuckDuckGo
│   ├── safe_filesystem.py     # Filesystem auditado
│   ├── file_ops.py            # Operaciones de archivos
│   ├── office_reader.py       # Office/PDF reader
│   ├── code_executor.py       # Ejecución segura (shell=False)
│   ├── crypto_data.py         # CoinGecko + DeFiLlama
│   └── git_ops.py             # GitHub API (PyGithub)
├── ui/
│   ├── server.py              # FastAPI + WebSockets
│   └── index.html             # Dashboard Tailwind
├── examples/                  # 7 scripts listos por pipeline
├── tests/                     # Tests unitarios
├── config.yaml                # Configuración global y pipelines
├── main.py                    # Entrada CLI
├── setup.py                   # Setup inicial + verificación
├── requirements.txt
├── .env.example
├── ARCHITECTURE.md            # Mapa 70 agentes → 12 pipelines
├── ROADMAP.md                 # Fases completadas y próximas
└── CONTRIBUTING.md
```

---

## 🚀 Instalación y uso

```bash
# 1. Clonar
git clone https://github.com/ariaslopez/orquestador-multiagente
cd orquestador-multiagente

# 2. Dependencias
pip install -r requirements.txt

# 3. Configurar
cp .env.example .env
# Editar .env con GROQ_API_KEY mínimo

# 4. Setup inicial
python setup.py

# 5. Verificar sistema
python main.py --doctor
```

### CLI

```bash
# Pipeline DEV
python main.py --task "API REST FastAPI para señales de trading" --type dev

# Pipeline RESEARCH
python main.py --task "Tesis de inversión Solana Q2 2026" --type research

# Pipeline OFFICE (con archivo)
python main.py --task "Analiza este backtest" --type office --file data.xlsx

# Pipeline QA
python main.py --task "Audita este módulo buscando vulnerabilidades" --type qa --file app/routes.py

# Clasificación automática (sin --type)
python main.py --task "¿Cuál es el Sharpe de este bot?"

# Modo interactivo
python main.py --interactive

# Dashboard web
python main.py --ui  # → http://127.0.0.1:8000
```

### Tests y ejemplos

```bash
# Tests unitarios (sin API keys, sin red)
pytest tests/ -v

# Ejemplos por pipeline
python examples/dev_example.py
python examples/research_example.py
python examples/content_example.py
```

---

## 💾 Memoria y estado

- **Local:** SQLite (`./data/claw_memory.db`) — sesiones recientes, disponible offline.
- **Nube:** Supabase opcional — historial sincronizado entre máquinas.
- El sistema recuerda tesis anteriores sobre un activo, evita duplicar proyectos y puede continuar trabajo interrumpido.

---

## 🔐 Seguridad

| Capa | Implementación |
|------|----------------|
| Paths protegidos | `C:/Windows`, `/etc`, `~/.ssh`, etc. definidos en `config.yaml` |
| Lista blanca de comandos | Solo `pip`, `pytest`, `git`, `python` con args controlados |
| Bloqueo de patrones peligrosos | `rm -rf`, `DROP TABLE`, pipe-to-bash, etc. |
| Shell injection | `shell=False` + `shlex.split` en todas las ejecuciones |
| Audit log | Cada operación registrada en `logs/` vía `audit_logger.py` |
| Git confirmación | `GITHUB_CONFIRM_BEFORE_PUSH=true` por defecto |
| `.env` permisos | `setup.py` aplica `chmod 600` en Unix/Linux/Mac |

### ⚠️ Riesgos conocidos

**Pipeline DEV ejecuta código en el host.** El `ExecutorAgent` usa el sandbox de CLAW como primera línea de defensa, no como aislamiento total a nivel OS. Para producción: ejecutar dentro de Docker efímero (Fase 11).

**Prompt injection.** El Maestro procesa texto libre del usuario sin sanitización de input. Limitar acceso a la API a usuarios de confianza hasta implementar auth (Fase 11).

---

## 📊 Evaluación del sistema

| Dimensión | Puntuación | Notas |
|-----------|-----------|-------|
| Arquitectura | 7.5/10 | Capas limpias, falta grafo dinámico |
| Seguridad | 8.0/10 | Mejor que CrewAI/LangGraph nativo |
| Confiabilidad prod. | 6.0/10 | Falta tests E2E + Docker sandbox |
| Razonamiento multi-agente | 6.5/10 | Solo DEV y RESEARCH son sub-pipelines reales |
| Developer Experience | 7.0/10 | CLI + UI + docs sólidos, falta tracing |
| **Global** | **7.0/10** | Proyecto personal avanzado, producción supervisada |

> Para llegar a 8.5+/10: tests E2E (Fase 10), tracing (Fase 10), expandir 5 pipelines macro (Fase 8).

---

## 📌 Estado y contribuciones

- Versión **1.0.0** — sistema estable, 7 pipelines operativos.
- El código y el `ROADMAP.md` son la fuente de verdad. Si hay discrepancia con cualquier otro doc, el código manda.
- Para contribuir: lee `CONTRIBUTING.md`.
- Issues y PRs bienvenidos para las fases 8–12.
