# 🤖 CLAW Agent System — Orquestador Multi-Agente

**Versión:** 2.4.0 · **Estado:** Producción supervisada · **Pipelines:** 12 activos · **MCPs:** 13 integrados

Sistema de inteligencia artificial multi-agente diseñado para automatizar trabajo de desarrollo, investigación, contenido, análisis, marketing, producto, diseño y seguridad. Un Maestro central clasifica cada tarea y la delega al pipeline correcto. Los agentes colaboran en secuencia o en paralelo, compartiendo un contexto tipado (`AgentContext`) y accediendo a 13 herramientas MCP externas.

> **Roadmap activo:** Ver `ROADMAP.md` para fases completadas, en progreso y próximas.
> **Mapa de agentes:** Ver `ARCHITECTURE.md` para el diseño completo de 70 agentes → 12 pipelines.
> **Manual técnico:** Ver `MANUAL.md` para guía completa de desarrollo y contribución.
> **Integraciones futuras:** Ver `FUTURE_INTEGRATIONS.md` para el blueprint de TweetBot + TradingBot v4-Pro en CLAW.

---

## 🧠 Arquitectura de alto nivel

```text
┌────────────────────────────────────────────────────────────────────────┐
│                          MAESTRO (LLM)                               │
│       Clasifica tarea → keywords + LLM → selecciona pipeline         │
└───┬──────┬──────┬──────┬──────┬──────┬──────┬──────┬──────┬─────────┘
    │      │      │      │      │      │      │      │
  DEV  RESEARCH CONTENT OFFICE  QA    PM  TRADING ANALYTICS ...+4
 6agt   4agt   5agt   3agt   5agt  4agt   4agt   3agt
 seq   par+seq  seq    seq    seq   seq    seq    seq
    │
    └───────────────────────────────────────────────────┐
                                                         ↓
                    ┌────────────────────────────────────────────┐
                    │            AgentContext tipado              │
                    │  ctx.mcp · ctx.memory · Logs · Audit       │
                    │   (SQLite + Supabase + 13 MCPs activos)     │
                    └────────────────────────────────────────────┘
```

### Componentes core

- `core/maestro.py` — Orquestador central: clasifica tarea y construye el pipeline.
- `core/pipeline_router.py` — Ejecutor: secuencial o `parallel_then_sequential`.
- `core/loop_controller.py` — Control de reintentos y recovery automático.
- `core/api_router.py` — Router de LLMs: Ollama (local) → Groq → Gemini → Hyperspace.
- `core/context.py` — `AgentContext` tipado: estado compartido entre agentes. **Incluye `ctx.mcp` → MCPHub.**
- `core/base_agent.py` — Contrato base con tracing automático + **memoria persistente pre/post run().**
- `infrastructure/memory_manager.py` — Memoria: SQLite local + sync a Supabase.
- `infrastructure/mcp_hub.py` — Proxy universal para 13 MCPs externos. **Conectado a AgentContext.**
- `infrastructure/audit_logger.py` — Tracing de agentes + métricas de pipeline.
- `infrastructure/input_sanitizer.py` — Anti prompt-injection (13 patrones, 3 capas).
- `infrastructure/security_sandbox.py` — Sandbox de filesystem y comandos.

### Estado de integración — Fases 12–14 (v2.2.2 → v2.4.0)

| Componente | Estado | Versión |
|---|---|---|
| MCPHub → AgentContext (`ctx.mcp`) | ✅ Completado | v2.2.2 |
| mcp_memory → BaseAgent pre/post run | ✅ Completado | v2.2.2 |
| Stubs duplicados en `agents/` raíz | ✅ Completado (tombstones) | v2.2.2 |
| `core/orchestrator.py` redundante | ✅ Resuelto (tombstone → Maestro) | v2.2.2 |
| `sequential_thinking` en PlannerAgent | ✅ Completado | v2.2.2 |
| WebScoutAgent real (brave_search + DDG) | ✅ Completado | v2.2.2 |
| DataAgent real (coingecko + supabase_mcp) | ✅ Completado | v2.2.2 |
| CoderAgent real (context7 + github_mcp) | ✅ Completado | v2.3.0 |
| ReportDistributorAgent real (supabase + slack) | ✅ Completado | v2.3.0 |
| Smoke tests 5/5 + lint CI | ✅ Completado | v2.4.0 |
| Rate limiting MCPHub (Brave, CoinGecko, OKX) | ✅ Completado | v2.4.0 |

---

## 🧩 Sistema de skills (Fase 17-A — en diseño)

Además de los 12 pipelines y 70 agentes, el proyecto incorporará un sistema de
skills declarativas que define **qué flujo seguir** para tareas recurrentes,
sin modificar el código Python existente.

```text
skills/
  shared/          # schema.md + safety_guards.md (reglas globales)
  dev/             # claude.md + skills/ (implement_feature, code_review, write_tests, refactor_module)
  research/        # claude.md + skills/ (web_research, competitor_analysis, summarize_sources)
  content/         # claude.md + skills/ (longform_to_social, newsletter_issue, landing_copy)
  office/          # claude.md + skills/ (meeting_notes, task_extraction, email_reply)
  qa/              # claude.md + skills/ (static_audit, test_plan, regression_suite)
  pm/              # claude.md + skills/ (roadmap_from_ideas, sprint_planning, backlog_grooming)
  analytics/       # claude.md + skills/ (kpi_report, funnel_analysis, cohort_analysis)
  marketing/       # claude.md + skills/ (campaign_brief, audience_persona, multi_channel_post, content_calendar)
  product/         # claude.md + skills/ (problem_interview, feature_brief, prioritization_rice)
  security_audit/  # claude.md + skills/ (threat_model, code_security_review, compliance_gap)
  design/          # claude.md + skills/ (ui_review, ux_audit, brand_system)
  # trading excluido del v1 de skills — se incorpora en v2 de Fase 17-A
```

- Cada `claude.md` define el rol del pipeline, agentes disponibles, MCPs permitidos y restricciones de seguridad.
- Cada skill (`.md`) describe inputs requeridos, agentes involucrados, pasos y formato de salida.
- Maestro leerá estas skills como guía de ejecución — los agentes Python no cambian.

> Diseño completo en `ARCHITECTURE.md` · Cómo escribir skills en `MANUAL.md`.

---

## 🔮 Integraciones futuras (Fase 20 — Q4 2026)

CLAW actuará como cerebro central de un ecosistema de tres sistemas especializados.
Ver el blueprint completo en [`FUTURE_INTEGRATIONS.md`](./FUTURE_INTEGRATIONS.md).

| Sistema | Rol en el ecosistema | Integración con CLAW | Fase |
|---|---|---|---|
| **TradingBot v4-Pro** | Motor de ejecución RL (forex + crypto) | MCP `trading_engine` → pipeline TRADING | Fase 20-A/B |
| **TweetBot Platform** | Generación y publicación de contenido en X | MCP `x_tweetbot` → pipeline CONTENT | Fase 20-C/D |
| **Dashboard unificado** | Vista única de todos los bots activos | Fase 15 UI + panel bots en Fase 20-E | Fase 15 + 20-E |

```text
                         CLAW v3.2.0
                    ┌────────────────────────┐
                    │     Maestro Orquestador    │
                    └────────┬─────────┬────────┘
                             │         │
             ┌────────────┘         └────────────┐
             ↓                         ↓
  ┌────────────────┐   ┌──────────────────┐
  │  TradingBot v4-Pro │   │  TweetBot Platform │
  │  Motor RL (forex/  │   │  Generación de     │
  │  crypto + MT5)     │   │  contenido para X  │
  └────────────────┘   └──────────────────┘
```

---

## 🌐 Stack de providers LLM

```
Provider primario : Ollama local (qwen2.5-coder:7b-q4_K_M)
Velocidad         : ~4-7 tok/s en CPU (Athlon 3000G + 24 GB RAM)
Contexto local    : 32,768 tokens
iGPU offload      : 4 capas → Vega 3 (+10-20% velocidad)
Fallback 1        : Groq llama-3.3-70b  (gratis, 131K ctx)
Fallback 2        : Gemini 2.0 Flash    (gratis, 1M ctx)
Fallback 3        : Hyperspace legacy
```

---

## 🔌 MCPs integrados (13)

| MCP | Categoría | Pipelines que lo usan | Requiere config |
|---|---|---|---|
| `brave_search` | 🔍 Search | research | `BRAVE_API_KEY` |
| `context7` | 🔍 Search | dev | `CONTEXT7_API_KEY` |
| `deepwiki` | 🔍 Search | qa, dev | `DEEPWIKI_API_KEY` |
| `supabase_mcp` | 🗄️ Data | analytics, trading | `SUPABASE_URL` ✅ |
| `mcp_memory` | 🧠 Memory | todos | — ninguna |
| `sequential_thinking` | 🤔 Reasoning | todos | — ninguna |
| `coingecko` | 📈 Trading | trading, research | opcional |
| `okx` | 📈 Trading | trading | `OKX_API_KEY` |
| `github_mcp` | 💻 Dev | dev, qa | `GITHUB_TOKEN` ✅ |
| `semgrep` | 🔒 Security | security_audit, qa | — ninguna |
| `playwright` | 🧪 QA | qa | — ninguna |
| `slack` | 📣 Notify | analytics, pm | `SLACK_BOT_TOKEN` |
| `n8n` | ⚙️ Automation | todos | `N8N_WEBHOOK_URL` |

> **Listos ahora mismo (sin configurar nada):** `mcp_memory`, `sequential_thinking`, `coingecko`, `semgrep`, `playwright`, `github_mcp`, `supabase_mcp`.

---

## 🔀 Pipelines disponibles (12 activos)

| Pipeline | Flag | Agentes | Descripción |
|---|---|---|---|
| **DEV** | `--type dev` | 6 · sec | Plan → código → review → seguridad → ejecución → git |
| **RESEARCH** | `--type research` | 4 · par+seq | Web + datos (paralelo) → análisis → tesis |
| **CONTENT** | `--type content` | 5 · sec | Topic → writer → editor → brand → scheduler |
| **OFFICE** | `--type office` | 3 · sec | Analiza Excel/PDF/Word/CSV → reporte ejecutivo |
| **QA** | `--type qa` | 5 · sec | Estática + bugs + seguridad + performance + tests |
| **PM** | `--type pm` | 4 · sec | Backlog, épicas, sprints y roadmap |
| **TRADING** | `--type trading` | 4 · sec | Backtest → Sharpe → drawdown → recomendaciones |
| **ANALYTICS** | `--type analytics` | 3 · sec | Consolida datos → insights → reporte ejecutivo |
| **MARKETING** | `--type marketing` | 4 · sec | Estrategia → copy → growth → métricas CAC/LTV |
| **PRODUCT** | `--type product` | 4 · sec | Mercado → feedback → priorización RICE → nudges |
| **SECURITY_AUDIT** | `--type security_audit` | 3 · sec | STRIDE → OWASP → GDPR/CCPA |
| **DESIGN** | `--type design` | 5 · sec | UI → UX → branding → a11y → prompts imagen |

`sec` = secuencial · `par+seq` = paralelo luego secuencial

---

## 📁 Estructura del proyecto

```text
orquestador-multiagente/
├── core/
│   ├── base_agent.py          # Contrato base — tracing + memoria episódica pre/post run()
│   ├── context.py             # AgentContext tipado — ctx.mcp (MCPHub) + inject_mcp()
│   ├── maestro.py             # Orquestador central (12 pipelines)
│   ├── api_router.py          # Router LLMs: Ollama → Groq → Gemini → Hyperspace
│   ├── pipeline_router.py     # Ejecutor: sequential / parallel_then_sequential
│   ├── loop_controller.py     # Control de reintentos y recovery
│   ├── task_packet.py         # TaskPacket tipado
│   └── groq_client.py         # Cliente Groq directo
├── agents/
│   ├── dev/                   # planner (v2 + sequential_thinking), coder (v2 + context7/github_mcp),
│   │                          #   reviewer, security, executor, git
│   ├── research/              # web_scout (v2 + brave_search), data (v2 + coingecko), analyst (v2), thesis (v2)
│   ├── content/               # topic, writer, editor, brand, scheduler
│   ├── office/                # file_reader, data_analyzer, report_writer
│   ├── qa/                    # static_analyzer, bug_hunter, security_reviewer,
│   │                          #   performance_profiler, test_generator
│   ├── pm/                    # requirements_parser, backlog_builder,
│   │                          #   sprint_planner, roadmap_generator
│   ├── trading/               # backtest_reader, metrics_calculator,
│   │                          #   risk_analyzer, strategy_advisor,
│   │                          #   data_agent (v2 + coingecko + supabase_mcp)
│   ├── analytics/             # data_collector, insight_generator,
│   │                          #   report_distributor (v2 + supabase_mcp + slack)
│   ├── marketing/             # strategy_agent, copy_agent, growth_agent, analytics_agent
│   ├── product/               # market_researcher, feedback_synthesizer,
│   │                          #   feature_prioritizer, nudge_designer
│   ├── security/              # threat_modeler, code_reviewer, compliance_checker
│   └── design/                # ui_agent, ux_agent, brand_agent, a11y_agent, prompt_engineer
├── skills/                    # Sistema de skills declarativas (Fase 17-A — pendiente)
│   ├── shared/                #   schema.md + safety_guards.md
│   └── <pipeline>/            #   claude.md + skills/*.md por pipeline
├── infrastructure/
│   ├── memory_manager.py      # SQLite + Supabase
│   ├── mcp_hub.py             # Proxy universal 13 MCPs — conectado a AgentContext
│   ├── security_layer.py      # 5 capas de protección
│   ├── security_sandbox.py    # Sandbox filesystem/comandos
│   ├── audit_logger.py        # Tracing de agentes + pipeline stats
│   ├── input_sanitizer.py     # Anti prompt-injection (13 patrones, 3 capas)
│   ├── state_manager.py       # Estado de sesión
│   └── output_manager.py      # Carpetas de salida
├── tools/
│   ├── web_search.py          # DuckDuckGo (fallback cuando brave_search no disponible)
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
│   ├── smoke/
│   │   ├── test_mcp_context.py          # Smoke: MCPHub + AgentContext (CI activo)
│   │   ├── test_pipeline_classification.py # Smoke: 12 pipelines + edge cases
│   │   ├── test_loop_controller_retry.py  # Smoke: modos SUPERVISED/AUTONOMOUS/PLAN_ONLY
│   │   ├── test_mcp_hub_fallback.py       # Smoke: MCP caído / env faltante / timeout
│   │   ├── test_supabase_persistence.py   # Smoke: sesión se guarda y recupera
│   │   └── test_api_router_fallback.py    # Smoke: Groq caído → fallback Gemini
│   ├── test_pipeline_imports.py   # 52 agentes + 12 pipelines
│   ├── test_e2e_pipelines.py      # 12 tests E2E con mock LLM
│   ├── test_integration_dev.py    # Integración pipeline DEV
│   ├── test_integration_research.py # Integración pipeline RESEARCH
│   └── test_input_sanitizer.py    # 12 unit tests del sanitizer
├── .github/
│   └── workflows/
│       ├── ci.yml                 # Smoke tests en cada push/PR
│       └── lint.yml               # Ruff en cada push/PR (Fase 14)
├── examples/                  # Scripts listos por pipeline
├── config.yaml                # Configuración global y 12 pipelines
├── main.py                    # Entrada CLI (VERSION=2.4.0)
├── setup.py                   # Setup inicial + verificación
├── requirements.txt
├── .env.example
├── README.md                  # Este archivo
├── ROADMAP.md                 # Fases completadas y próximas
├── ARCHITECTURE.md            # Mapa 70 agentes → 12 pipelines + sistema de skills
├── MANUAL.md                  # Manual técnico de desarrollo
└── FUTURE_INTEGRATIONS.md     # Blueprint TweetBot + TradingBot v4-Pro en CLAW
```

---

## ✅ PRs Fases 12–14 completados (v2.2.2 → v2.4.0)

| PR | Título | Estado |
|---|---|---|
| **PR-1** | `feat: conectar MCPHub + mcp_memory a AgentContext y BaseAgent` | ✅ Fusionado (v2.2.2) |
| **PR-2** | `chore: eliminar stubs duplicados y archivos redundantes` | ✅ Fusionado (v2.2.2) |
| **PR-3** | `feat: WebScoutAgent + PlannerAgent + DataAgent v2 con MCPs` | ✅ Fusionado (v2.2.2) |
| **PR-4** | `test: smoke test MCPHub + workflow CI básico` | ✅ Fusionado (v2.2.2) |
| **PR-5** | `feat: CoderAgent real con context7 + github_mcp` | ✅ Fusionado (v2.3.0) |
| **PR-6** | `feat: ReportDistributorAgent real con supabase_mcp + slack` | ✅ Fusionado (v2.3.0) |
| **PR-7** | `test: smoke tests completos (5/5) + rate limiting MCPHub` | ✅ Fusionado (v2.4.0) |
| **PR-8** | `ci: lint workflow con ruff` | ✅ Fusionado (v2.4.0) |

**Próximo (Fase 15):**
- `feat: Dashboard UI funcional — WebSocket + panel pipelines + panel bots`

---

## 🚀 Instalación y uso

```bash
# 1. Clonar
git clone https://github.com/ariaslopez/orquestador-multiagente
cd orquestador-multiagente

# 2. Entorno virtual
python -m venv venv
source venv/bin/activate       # Linux/Mac
# venv\Scripts\activate         # Windows

# 3. Dependencias
pip install -r requirements.txt

# 4. Configurar
cp .env.example .env
# Mínimo requerido: GROQ_API_KEY
# Opcional pero recomendado: BRAVE_API_KEY, GITHUB_TOKEN, SUPABASE_URL

# 5. Verificar setup
python setup.py

# 6. Ejecutar
python main.py --task "Analiza el rendimiento de BTC/USDT últimas 24h" --type trading
python main.py --task "Crea tests unitarios para api_router.py" --type qa
python main.py --task "Investiga mejores prácticas de RL para trading" --type research
```

### Uso del Dashboard UI

```bash
cd ui && uvicorn server:app --reload --port 8000
# Abrir: http://localhost:8000
```

---

## ⚙️ Configuración de hardware

```env
# CPU puro (configuración actual — Athlon 3000G + 24 GB RAM)
OLLAMA_HW_PROFILE=cpu_24gb
LOCAL_GPU_LAYERS=4          # iGPU Vega 3

# RTX 3070 / RX 6700 XT (8 GB VRAM) — upgrade sin cambios de código
OLLAMA_HW_PROFILE=gpu_8gb
LOCAL_GPU_LAYERS=33

# RTX 4070+ (12-16 GB VRAM)
OLLAMA_HW_PROFILE=gpu_16gb
LOCAL_GPU_LAYERS=43
LOCAL_CONTEXT_SIZE=65536
```

---

## 🤝 Contribución

Ver `MANUAL.md` para la guía completa: convenciones de código, cómo agregar un nuevo pipeline, cómo agregar un nuevo MCP, cómo escribir skills, estructura de tests.
