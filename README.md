# 🤖 CLAW Agent System — Orquestador Multi-Agente

**Versión:** 2.1.0 · **Estado:** Producción supervisada · **Pipelines:** 12 activos · **MCPs:** 13 integrados

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
                    │  Memoria · Logs · Observability · MCPHub   │
                    │        (SQLite + Supabase + 13 MCPs)        │
                    └────────────────────────────────────────────┘
```

### Componentes core

- `core/maestro.py` — Orquestador central: clasifica tarea y construye el pipeline.
- `core/pipeline_router.py` — Ejecutor: secuencial o `parallel_then_sequential`.
- `core/loop_controller.py` — Control de reintentos y recovery automático.
- `core/api_router.py` — Router de LLMs: Ollama (local) → Groq → Gemini → Hyperspace.
- `core/context.py` — `AgentContext` tipado: estado compartido entre agentes.
- `core/base_agent.py` — Contrato base con tracing automático.
- `infrastructure/memory_manager.py` — Memoria: SQLite local + sync a Supabase.
- `infrastructure/mcp_hub.py` — Proxy universal para 13 MCPs externos.
- `infrastructure/audit_logger.py` — Tracing de agentes + métricas de pipeline.
- `infrastructure/input_sanitizer.py` — Anti prompt-injection (13 patrones, 3 capas).
- `infrastructure/security_sandbox.py` — Sandbox de filesystem y comandos.

### ⚠️ Estado crítico conocido (pendiente)

> `MCPHub` está implementado en `infrastructure/mcp_hub.py` pero **aún no está conectado a `AgentContext`**.
> Los 13 MCPs no son accesibles por los agentes hasta completar el Paso 1 de la Fase 12.
> Ver `ROADMAP.md → Fase 12` para el plan de conexión.

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
│   ├── base_agent.py          # Contrato base — tracing automático
│   ├── context.py             # AgentContext tipado (estado compartido)
│   ├── maestro.py             # Orquestador central (12 pipelines)
│   ├── api_router.py          # Router LLMs: Ollama → Groq → Gemini → Hyperspace
│   ├── pipeline_router.py     # Ejecutor: sequential / parallel_then_sequential
│   ├── loop_controller.py     # Control de reintentos y recovery
│   ├── task_packet.py         # TaskPacket tipado
│   └── groq_client.py         # Cliente Groq directo
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
│   ├── mcp_hub.py             # ⚠️ Proxy universal 13 MCPs — pendiente conectar a AgentContext
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
# Opcional pero recomendado: OLLAMA_ENABLED=true

# 5. Verificar sistema
python main.py --doctor
```

### CLI completa

```bash
# Ejecución básica
python main.py --task "API REST FastAPI para señales de trading" --type dev
python main.py --task "Tesis de inversión Solana Q2 2026" --type research
python main.py --task "Analiza este backtest" --type office --file data.xlsx
python main.py --task "Audita este módulo" --type qa --file app/routes.py

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
pytest tests/ -v
pytest tests/test_pipeline_imports.py -v
pytest tests/test_e2e_pipelines.py -v
pytest tests/test_input_sanitizer.py -v
```

---

## 💾 Variables de entorno

```env
# LLM — mínimo requerido
GROQ_API_KEY=tu_clave_groq

# LLM — Ollama local (recomendado)
OLLAMA_ENABLED=true
OLLAMA_HW_PROFILE=cpu_24gb

# LLM — fallbacks
GEMINI_API_KEY=tu_clave

# Memoria cloud
SUPABASE_URL=...
SUPABASE_KEY=...

# MCPs — agregar según necesites
BRAVE_API_KEY=your_key
CONTEXT7_API_KEY=your_key
DEEPWIKI_API_KEY=your_key
OKX_API_KEY=your_key
GITHUB_TOKEN=your_token
SLACK_BOT_TOKEN=xoxb-...
N8N_WEBHOOK_URL=https://...
COINGECKO_API_KEY=your_key   # opcional
MCP_TIMEOUT=30
```

---

## 🔐 Seguridad

| Capa | Implementación |
|---|---|
| Paths protegidos | `C:/Windows`, `/etc`, `~/.ssh` — `config.yaml` |
| Lista blanca comandos | Solo `pip`, `pytest`, `git`, `python`, `node`, `cargo` |
| Shell injection | `shell=False` + `shlex.split` en todas las ejecuciones |
| Prompt injection | `input_sanitizer.py` — 3 capas, 13 patrones |
| Audit log | Cada operación registrada en `logs/` vía `audit_logger.py` |
| Git confirmación | `GITHUB_CONFIRM_BEFORE_PUSH=true` por defecto |

> ⚠️ **Pipeline DEV ejecuta código en el host.** El sandbox actual es la primera línea de defensa, no aislamiento a nivel OS. Para producción real: Docker efímero (Fase 15).

---

## 📊 Madurez del sistema (v2.1.0)

| Componente | Estado | Notas |
|---|---|---|
| Maestro + clasificación | 🟢 Sólido | 12 pipelines, keywords + LLM |
| LoopController | 🟢 Sólido | Retry + recovery automático |
| PipelineRouter | 🟢 Sólido | Sequential + parallel_then_sequential |
| AuditLogger + logs | 🟢 Sólido | Tracing por agente |
| MemoryManager | 🟢 Sólido | SQLite + Supabase sync |
| API Router (LLMs) | 🟢 Sólido | 4 providers + fallback automático |
| MCPHub (13 MCPs) | 🟡 Implementado | ⚠️ Pendiente conectar a AgentContext |
| Agentes individuales | 🟡 Parcial | Stubs en raíz, sub-agentes en directorios |
| Tests | 🟡 Básico | E2E + unit; sin smoke tests críticos |
| Dashboard UI | ❓ Desconocido | ui/server.py + ui/index.html — verificar estado |

---

## 📌 Próximos pasos

Ver `ROADMAP.md → Fase 12` para el plan detallado. En resumen:

1. **Conectar MCPHub a AgentContext** — desbloquea 13 MCPs para todos los agentes
2. **Implementar 5 agentes core reales** — WebScout, Planner, Coder, Data, ReportDistributor
3. **5 smoke tests críticos** — clasificación, retry, MCP fallback, persistencia, LLM fallback
4. **Limpiar deuda técnica** — stubs en raíz, orchestrator.py/pipeline.py redundantes
5. **Dashboard UI funcional** — métricas en tiempo real desde Supabase
