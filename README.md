# 🤖 CLAW Agent System — Orquestador Multi-Agente

**Versión:** 2.0.0 · **Estado:** Producción supervisada · **Pipelines:** 12 activos

Sistema de inteligencia artificial multi-agente diseñado para automatizar trabajo de desarrollo, investigación, contenido, análisis, marketing, producto, diseño y seguridad. Un Maestro central clasifica cada tarea y la delega al pipeline correcto. Los agentes colaboran en secuencia o en paralelo, compartiendo un contexto tipado (`AgentContext`).

> **Roadmap activo:** Ver `ROADMAP.md` para fases completadas y próximas.
> **Mapa de agentes:** Ver `ARCHITECTURE.md` para el diseño completo de 70 agentes → 12 pipelines.

---

## 🧠 Arquitectura de alto nivel

```text
┌──────────────────────────────────────────────────────────────────┐
│                        MAESTRO (LLM)                             │
│      Clasifica tarea → keywords + LLM → selecciona pipeline      │
└───┬──────┬──────┬──────┬──────┬──────┬──────┬──────┬──────┬─────┘
    │      │      │      │      │      │      │      │      │
  DEV  RESEARCH CONTENT OFFICE  QA    PM  TRADING ANALYTICS ...+4
 6agt   4agt   5agt   3agt   5agt  4agt   4agt   3agt
 seq   par+seq  seq    seq    seq   seq    seq    seq
    │
    └─────────────────────────────────────────────┐
                                                  ▼
                         ┌────────────────────────────────┐
                         │       AgentContext tipado       │
                         │  Memoria · Logs · Observability │
                         │     (SQLite + Supabase)         │
                         └────────────────────────────────┘
```

- `core/maestro.py` — Orquestador central: clasifica tarea y construye el pipeline.
- `core/pipeline_router.py` — Ejecutor: secuencial o `parallel_then_sequential`.
- `core/api_router.py` — Router de LLMs: Groq (principal) → Gemini (fallback) → Hyperspace (offline).
- `infrastructure/memory_manager.py` — Memoria: SQLite local + sync opcional a Supabase.
- `infrastructure/security_sandbox.py` — Sandbox de filesystem y comandos con audit log.
- `infrastructure/audit_logger.py` — Tracing de agentes + métricas de pipeline.
- `infrastructure/input_sanitizer.py` — Anti prompt-injection (13 patrones, 3 capas).

---

## 🔀 Pipelines disponibles (12 activos)

| Pipeline | Flag | Agentes | Descripción |
|----------|------|---------|-------------|
| **DEV** | `--type dev` | 6 · sec | Genera proyectos: plan → código → review → seguridad → ejecución → git |
| **RESEARCH** | `--type research` | 4 · par+seq | Tesis de inversión: web + datos (paralelo) → análisis → tesis |
| **CONTENT** | `--type content` | 5 · sec | Contenido crypto: topic → writer → editor → brand → scheduler |
| **OFFICE** | `--type office` | 3 · sec | Analiza Excel, PDF, Word, CSV y genera reporte ejecutivo |
| **QA** | `--type qa` | 5 · sec | Auditoría: estática, bugs, seguridad, performance, tests |
| **PM** | `--type pm` | 4 · sec | Backlog, épicas, sprints y roadmap desde descripción libre |
| **TRADING** | `--type trading` | 4 · sec | Analytics de bots: backtest, Sharpe, drawdown, recomendaciones |
| **ANALYTICS** | `--type analytics` | 3 · sec | Consolida datos, extrae insights y genera reporte ejecutivo |
| **MARKETING** | `--type marketing` | 4 · sec | Estrategia, copy, growth loops y métricas CAC/LTV |
| **PRODUCT** | `--type product` | 4 · sec | Investigación de mercado, feedback, priorización RICE y nudges |
| **SECURITY_AUDIT** | `--type security_audit` | 3 · sec | Modelado STRIDE, code review OWASP, compliance GDPR/CCPA |
| **DESIGN** | `--type design` | 5 · sec | Sistema UI, arquitectura UX, branding, a11y y prompts de imagen |

`sec` = secuencial · `par+seq` = paralelo luego secuencial

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
# .env mínimo para arrancar
GROQ_API_KEY=tu_clave_groq       # Obligatorio — https://console.groq.com
GEMINI_API_KEY=tu_clave          # Opcional (fallback LLM)
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
│   ├── base_agent.py          # Contrato base — tracing automático
│   ├── context.py             # AgentContext tipado (estado compartido)
│   ├── maestro.py             # Orquestador central (12 pipelines)
│   ├── api_router.py          # Router LLMs: Groq → Gemini → Hyperspace
│   └── pipeline_router.py     # Ejecutor: sequential / parallel_then_sequential
├── agents/
│   ├── dev/                   # planner, coder, reviewer, security, executor, git
│   ├── research/              # web_scout, data, analyst, thesis
│   ├── content/               # topic, writer, editor, brand, scheduler
│   ├── office/                # file_reader, data_analyzer, report_writer
│   ├── qa/                    # static_analyzer, bug_hunter, security_reviewer,
│   │                          #   performance_profiler, test_generator
│   ├── pm/                    # requirements_parser, backlog_builder,
│   │                          #   sprint_planner, roadmap_generator
│   ├── trading/               # backtest_reader, metrics_calculator,
│   │                          #   risk_analyzer, strategy_advisor
│   ├── analytics/             # data_collector, insight_generator, report_distributor
│   ├── marketing/             # strategy_agent, copy_agent, growth_agent, analytics_agent
│   ├── product/               # market_researcher, feedback_synthesizer,
│   │                          #   feature_prioritizer, nudge_designer
│   ├── security/              # threat_modeler, code_reviewer, compliance_checker
│   └── design/                # ui_agent, ux_agent, brand_agent, a11y_agent, prompt_engineer
├── infrastructure/
│   ├── memory_manager.py      # SQLite + Supabase
│   ├── security_layer.py      # 5 capas de protección
│   ├── security_sandbox.py    # Sandbox filesystem/comandos
│   ├── audit_logger.py        # Tracing de agentes + pipeline stats
│   ├── input_sanitizer.py     # Anti prompt-injection (13 patrones, 3 capas)
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
│   ├── server.py              # FastAPI + WebSockets + /api/metrics
│   └── index.html             # Dashboard Tailwind (12 pipelines)
├── tests/
│   ├── test_pipeline_imports.py   # 52 agentes + 12 pipelines
│   ├── test_e2e_pipelines.py      # 12 tests E2E con mock LLM
│   └── test_input_sanitizer.py    # 12 unit tests del sanitizer
├── examples/                  # Scripts listos por pipeline
├── config.yaml                # Configuración global y 12 pipelines
├── main.py                    # Entrada CLI (--type acepta 12 pipelines)
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

# 2. Entorno virtual (recomendado)
python -m venv venv && source venv/bin/activate  # Linux/Mac
# python -m venv venv && venv\Scripts\activate   # Windows

# 3. Dependencias
pip install -r requirements.txt

# 4. Configurar
cp .env.example .env
# Editar .env — mínimo: GROQ_API_KEY

# 5. Verificar sistema
python main.py --doctor
```

### CLI — todos los pipelines

```bash
# Pipelines originales
python main.py --task "API REST FastAPI para señales de trading" --type dev
python main.py --task "Tesis de inversión Solana Q2 2026" --type research
python main.py --task "Analiza este backtest" --type office --file data.xlsx
python main.py --task "Audita este módulo" --type qa --file app/routes.py

# Pipelines Fase 9 (nuevos en v2.0.0)
python main.py --task "Reporte KPIs semana" --type analytics
python main.py --task "Plan de lanzamiento SaaS B2B" --type marketing
python main.py --task "Roadmap Q3 con priorización RICE" --type product
python main.py --task "Audita seguridad de esta API" --type security_audit
python main.py --task "Sistema de diseño para app fintech" --type design

# Clasificación automática (sin --type)
python main.py --task "¿Cuál es el Sharpe de este bot?"

# Modos especiales
python main.py --interactive          # Loop de tareas en terminal
python main.py --ui                   # Dashboard → http://127.0.0.1:8000
python main.py --doctor               # Diagnóstico completo del sistema
python main.py --history              # Últimas 20 sesiones
python main.py --usage                # Tokens y costos acumulados
```

### Tests

```bash
# Sin API keys, sin red — usa mock LLM
pytest tests/ -v

# Por módulo
pytest tests/test_pipeline_imports.py -v   # Verifica 52 agentes + 12 pipelines
pytest tests/test_e2e_pipelines.py -v      # 12 tests E2E
pytest tests/test_input_sanitizer.py -v    # Seguridad de inputs
```

---

## 💾 Memoria y estado

- **Local:** SQLite (`./data/claw_memory.db`) — sesiones recientes, disponible offline.
- **Nube:** Supabase opcional — historial sincronizado entre máquinas.
- El sistema recuerda tesis anteriores sobre un activo, evita duplicar proyectos y puede continuar trabajo interrumpido.
- **Observability:** `GET /api/metrics` en el dashboard expone stats de pipeline en tiempo real.

---

## 🔐 Seguridad

| Capa | Implementación |
|------|----------------|
| Paths protegidos | `C:/Windows`, `/etc`, `~/.ssh`, etc. — `config.yaml` |
| Lista blanca de comandos | Solo `pip`, `pytest`, `git`, `python`, `node`, `cargo` |
| Bloqueo de patrones peligrosos | `rm -rf`, `DROP TABLE`, pipe-to-bash, etc. |
| Shell injection | `shell=False` + `shlex.split` en todas las ejecuciones |
| Prompt injection | `input_sanitizer.py` — 3 capas, 13 patrones |
| Audit log | Cada operación registrada en `logs/` vía `audit_logger.py` |
| Git confirmación | `GITHUB_CONFIRM_BEFORE_PUSH=true` por defecto en `.env.example` |
| `.env` permisos | `setup.py` aplica `chmod 600` en Unix/Linux/Mac |

### ⚠️ Riesgos conocidos

**Pipeline DEV ejecuta código en el host.** El sandbox de CLAW es la primera línea de defensa, no aislamiento total a nivel OS. Para producción: ejecutar dentro de Docker efímero (Fase 11).

---

## 📊 Evaluación del sistema (v2.0.0)

| Dimensión | Puntuación | Notas |
|-----------|-----------|-------|
| DX / CLI | 8.5/10 | 12 flags, doctor, interactivo, UI, history, usage |
| Arquitectura | 8.0/10 | 5 capas limpias, AgentContext tipado, router paralelo |
| Seguridad | 7.5/10 | 5 capas + input_sanitizer; sandbox sin Docker aún |
| Confiabilidad | 6.5/10 | Retry + fallback LLM; Docker sandbox en Fase 11 |
| Testing | 5.5/10 | E2E + unit con mock LLM; sin CI/CD aún |
| **Global** | **6.9/10** | Producción supervisada — Fase 11 lleva a 8.0+ |

---

## 📌 Estado y hoja de ruta

- **v2.0.0** — 12 pipelines operativos, 70 agentes, observability, input sanitizer.
- **Fase 11 (próxima):** Docker sandbox, Fly.io deploy, auth en `/api/task`, Supabase como fuente principal.
- El código y `ROADMAP.md` son la fuente de verdad. Si hay discrepancia con cualquier otro doc, el código manda.
- Issues y PRs bienvenidos.
