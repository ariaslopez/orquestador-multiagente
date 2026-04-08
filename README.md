# 🤖 CLAW Agent System — Orquestador Multi-Agente

**Versión:** 2.2.0-dev · **Estado:** Producción supervisada · **Pipelines:** 12 activos · **MCPs:** 13 integrados

Sistema de inteligencia artificial multi-agente diseñado para automatizar trabajo de desarrollo, investigación, contenido, análisis, marketing, producto, diseño y seguridad. Un Maestro central clasifica cada tarea y la delega al pipeline correcto. Los agentes colaboran en secuencia o en paralelo, compartiendo un contexto tipado (`AgentContext`) y accediendo a 13 herramientas MCP externas.

> **Roadmap activo:** Ver `ROADMAP.md` para fases completadas, en progreso y próximas.
> **Mapa de agentes:** Ver `ARCHITECTURE.md` para el diseño completo de 70 agentes → 12 pipelines.
> **Manual técnico:** Ver `MANUAL.md` para guía completa de desarrollo y contribución.

---

## 🧠 Arquitectura de alto nivel

```text
┌──────────────────────────────────────────────────────────────────────┐
│                          MAESTRO (LLM)                               │
│       Clasifica tarea → keywords + LLM → selecciona pipeline         │
└───┬──────┬──────┬──────┬──────┬──────┬──────┬──────┬──────┬─────────┘
    │      │      │      │      │      │      │      │      │
  DEV  RESEARCH CONTENT OFFICE  QA    PM  TRADING ANALYTICS ...+4
 6agt   4agt   5agt   3agt   5agt  4agt   4agt   3agt
 seq   par+seq  seq    seq    seq   seq    seq    seq
    │
    └────────────────────────────────────────────────────┐
                                                         ▼
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

### 🚧 Estado de integración (Fase 12 en progreso)

| Componente | Estado | Notas |
|---|---|---|
| MCPHub → AgentContext (`ctx.mcp`) | 🟠 En progreso | PR-1: cambio en `context.py` + `maestro.py` |
| mcp_memory → BaseAgent pre/post run | 🟠 En progreso | PR-1: cambio en `base_agent.py` |
| Stubs duplicados en `agents/` raíz | 🟠 En progreso | PR-2: 6 archivos a eliminar/fusionar |
| `core/orchestrator.py` redundante | 🟠 En progreso | PR-2: evaluar y eliminar |
| `sequential_thinking` en PlannerAgent | 🔴 Pendiente | PR-3: requiere ctx.mcp disponible |
| WebScoutAgent real | 🔴 Pendiente | PR-3: brave_search + mcp_memory |
| DataAgent real | 🔴 Pendiente | PR-3: coingecko + supabase_mcp |
| Smoke tests críticos | 🔴 Pendiente | PR-4: 5 tests + CI básico |

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
| `supabase_mcp` | 🗄️ Data | analytics | `SUPABASE_URL` ✅ |
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
│   ├── base_agent.py          # Contrato base — tracing + memoria pre/post run()
│   ├── context.py             # AgentContext tipado — incluye ctx.mcp (MCPHub)
│   ├── maestro.py             # Orquestador central (12 pipelines)
│   ├── api_router.py          # Router LLMs: Ollama → Groq → Gemini → Hyperspace
│   ├── pipeline_router.py     # Ejecutor: sequential / parallel_then_sequential
│   ├── loop_controller.py     # Control de reintentos y recovery
│   ├── task_packet.py         # TaskPacket tipado
│   └── groq_client.py         # Cliente Groq directo
├── agents/
│   ├── dev/                   # planner, coder, reviewer, security, executor, git
│   ├── research/              # web_scout (🟠 real en PR-3), data, analyst, thesis
│   ├── content/               # topic, writer, editor, brand, scheduler
│   ├── office/                # file_reader, data_analyzer, report_writer
│   ├── qa/                    # static_analyzer, bug_hunter, security_reviewer,
│   │                          #   performance_profiler, test_generator
│   ├── pm/                    # requirements_parser, backlog_builder,
│   │                          #   sprint_planner, roadmap_generator
│   ├── trading/               # backtest_reader, metrics_calculator,
│   │                          #   risk_analyzer, strategy_advisor
│   │                          #   data_agent (🟠 real en PR-3 via coingecko+supabase)
│   ├── analytics/             # data_collector, insight_generator, report_distributor
│   ├── marketing/             # strategy_agent, copy_agent, growth_agent, analytics_agent
│   ├── product/               # market_researcher, feedback_synthesizer,
│   │                          #   feature_prioritizer, nudge_designer
│   ├── security/              # threat_modeler, code_reviewer, compliance_checker
│   └── design/                # ui_agent, ux_agent, brand_agent, a11y_agent, prompt_engineer
├── infrastructure/
│   ├── memory_manager.py      # SQLite + Supabase
│   ├── mcp_hub.py             # Proxy universal 13 MCPs — conectado a AgentContext en PR-1
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
│   ├── test_pipeline_imports.py   # 52 agentes + 12 pipelines
│   ├── test_e2e_pipelines.py      # 12 tests E2E con mock LLM
│   └── test_input_sanitizer.py    # 12 unit tests del sanitizer
├── examples/                  # Scripts listos por pipeline
├── config.yaml                # Configuración global y 12 pipelines
├── main.py                    # Entrada CLI
├── setup.py                   # Setup inicial + verificación
├── requirements.txt
├── .env.example
├── README.md                  # Este archivo
├── ROADMAP.md                 # Fases completadas y próximas
├── ARCHITECTURE.md            # Mapa 70 agentes → 12 pipelines
└── MANUAL.md                  # Manual técnico de desarrollo
```

---

## 🔧 Próximos PRs (plan de construcción activo)

El sistema tiene toda la infraestructura construida. Los siguientes PRs conectan las piezas existentes sin reescribir nada estructural.

```
PR-1 (MCPHub + memoria en AgentContext/BaseAgent)  ← CRÍTICO, primer PR
    ↓ desbloquea
PR-3 (WebScoutAgent + PlannerAgent + DataAgent reales)
    ↑ independiente
PR-2 (limpieza de stubs y redundancias)
    ↓ todo junto habilita
PR-4 (smoke tests + CI/CD básico)
```

| PR | Título | Archivos clave | Prioridad |
|---|---|---|---|
| **PR-1** | `feat: conectar MCPHub + mcp_memory a AgentContext y BaseAgent` | `context.py`, `base_agent.py`, `maestro.py` | 🔴 CRÍTICO |
| **PR-2** | `chore: eliminar stubs duplicados y archivos redundantes` | `agents/*.py` raíz, `core/orchestrator.py` | 🟠 Alta |
| **PR-3** | `feat: WebScoutAgent + PlannerAgent + DataAgent reales` | `agents/research/web_scout.py`, `agents/dev/planner_agent.py`, `agents/trading/data_agent.py` | 🟠 Alta |
| **PR-4** | `test: smoke tests críticos + workflow CI básico` | `tests/test_smoke_*.py`, `.github/workflows/` | 🟡 Media |

> Ver `ROADMAP.md` para el detalle completo de cada fase y deuda técnica priorizada.

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

Ver `MANUAL.md` para la guía completa: convenciones de código, cómo agregar un nuevo pipeline, cómo agregar un nuevo MCP, estructura de tests.
