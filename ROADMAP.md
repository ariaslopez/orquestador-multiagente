# ROADMAP — CLAW Agent System

## Estado actual: v2.3.1

> Última actualización: Abril 8, 2026 — Auditoría de pipelines críticos + propuesta sub-agentes colaboradores

---

## ✅ Fases completadas (v1.0.0 → v2.3.0)

### Fase 1: DEV Pipeline
- [x] `agents/dev/planner_agent.py`
- [x] `agents/dev/coder_agent.py`
- [x] `agents/dev/reviewer_agent.py`
- [x] `agents/dev/security_agent.py`
- [x] `agents/dev/executor_agent.py`
- [x] `agents/dev/git_agent.py`

### Fase 2: Research, Content y Office
- [x] `agents/research/` — 4 agentes (web_scout, data, analyst, thesis)
- [x] `agents/content/` — sub-pipeline expandido
- [x] `agents/office/` — sub-pipeline expandido

### Fase 3: QA, Trading y PM
- [x] `agents/qa/` — 5 agentes
- [x] `agents/trading/` — 4 agentes
- [x] `agents/pm/` — 4 agentes

### Fase 4–7: Infrastructure, Tools, UI, Docs
- [x] `infrastructure/` — 8 módulos (incluyendo mcp_hub.py)
- [x] `tools/` — 7 tools
- [x] `ui/server.py` + `ui/index.html`
- [x] `README.md`, `ARCHITECTURE.md`, `CONTRIBUTING.md`, `MANUAL.md`
- [x] `examples/` — 12 ejemplos por pipeline

### Fase 8: Sub-pipelines reales
- [x] CONTENT (5 agentes), QA (5), PM (4), OFFICE (3), TRADING (4)

### Fase 9: 5 pipelines nuevos
- [x] ANALYTICS (3), MARKETING (4), PRODUCT (4), SECURITY_AUDIT (3), DESIGN (5)
- [x] Clasificador expandido a 12 pipelines en `core/maestro.py`

### Fase 10: Observabilidad y tests E2E
- [x] Tracing automático en `BaseAgent` + `audit_logger.py`
- [x] Input sanitizer (3 capas, 13 patrones)
- [x] 12 tests E2E con mock LLM
- [x] Dashboard métricas en `GET /api/metrics`

### Fase 11: LLM Local-First + GPU-Ready
- [x] `core/api_router.py` — estrategia `local_first` con 4 providers
- [x] Perfiles de hardware: `cpu_24gb` → `gpu_8gb` → `gpu_16gb` → `gpu_24gb`
- [x] Ollama como provider primario con offload a iGPU Vega 3
- [x] `infrastructure/mcp_hub.py` — proxy universal para 13 MCPs
- [x] MCPs integrados: brave_search, context7, deepwiki, supabase_mcp, mcp_memory,
      sequential_thinking, coingecko, okx, github_mcp, semgrep, playwright, slack, n8n
- [x] `.env.example` actualizado con variables de MCP
- [x] Bugs críticos corregidos: double retry silencioso, race condition singleton,
      costo contra provider equivocado, @retry sobre async def

### ✅ Fase 12: Activar lo que ya existe — COMPLETADA en v2.2.2

> **Completada:** Abril 8, 2026

#### Paso 1 — Conectar MCPHub a AgentContext
- [x] `AgentContext.inject_mcp()` — inyecta MCPHub en el contexto
- [x] Helpers `ctx.is_mcp_available()` y `ctx.mcp_call()` disponibles para todos los agentes
- [x] Maestro llama `ctx.inject_mcp(hub)` al construir cada pipeline

#### Paso 2 — Resolver duplicidad de agentes
- [x] `agents/trading_agent.py` → tombstone / redirect a `agents/trading/`
- [x] `agents/qa_agent.py` → tombstone / redirect a `agents/qa/`
- [x] `agents/content_agent.py` → tombstone / redirect a `agents/content/`
- [x] `agents/pm_agent.py` → tombstone / redirect a `agents/pm/`
- [x] `agents/office_agent.py` → tombstone / redirect a `agents/office/`
- [x] `agents/doc_agent.py` → evaluado y convertido a tombstone
- [x] `core/maestro.py` importa únicamente desde los directorios correctos

#### Paso 3 — Limpiar archivos redundantes
- [x] `core/orchestrator.py` → tombstone / alias de compatibilidad hacia Maestro
- [x] `core/pipeline.py` → tombstone / alias de compatibilidad hacia PipelineRouter
- [x] Imports actualizados en archivos que los referencian

#### Paso 4 — Conectar mcp_memory en BaseAgent
- [x] `base_agent.py` → hook `_before_run()`: recupera contexto previo de `mcp_memory`
- [x] `base_agent.py` → hook `_after_run()`: guarda conclusiones en `mcp_memory`
- [x] Todos los agentes heredan memoria episódica persistente automáticamente

#### Paso 5 — Conectar sequential_thinking en PlannerAgent
- [x] `agents/dev/planner_agent.py` → usa `ctx.mcp_call("sequential_thinking", ...)` como paso 1
- [x] Fallback a subtareas desde plan JSON cuando el MCP no está disponible

### ✅ Fase 13: Implementar los 5 agentes core reales — COMPLETADA en v2.3.0

> **Completada:** Abril 8, 2026

| # | Agente | Pipeline | MCPs que usa | Estado |
|---|---|---|---|---|
| 1 | **WebScoutAgent** | research | brave_search + mcp_memory | ✅ Completado (v2) |
| 2 | **PlannerAgent** | dev + todos | sequential_thinking + mcp_memory | ✅ Completado (v2) |
| 3 | **DataAgent** | trading | coingecko + okx + supabase_mcp | ✅ Completado (v2) |
| 4 | **CoderAgent** | dev | context7 + github_mcp | ✅ Completado (v2) |
| 5 | **ReportDistributorAgent** | analytics | supabase_mcp + slack | ✅ Completado (v2) |

- [x] Implementar `WebScoutAgent` real con brave_search + fallback DuckDuckGo
- [x] Implementar `PlannerAgent` real con sequential_thinking + memoria episódica
- [x] Implementar `DataAgent` real con coingecko + supabase_mcp
- [x] Implementar `CoderAgent` real con context7 + github_mcp
- [x] Implementar `ReportDistributorAgent` real con supabase_mcp + slack

### ✅ Auditoría v2.3.1 — COMPLETADA Abril 8, 2026

> **Alcance:** revisión de código, documentación, tests y propuesta de sub-agentes colaboradores
> para los 6 pipelines críticos: DEV, RESEARCH, QA, TRADING, ANALYTICS, SECURITY_AUDIT.

**Hallazgos clave:**
- Núcleo de orquestación, MCPHub, memoria, seguridad y CLI: sólidos y coherentes con v2.3.0.
- Pipelines DEV y RESEARCH: mayor madurez; cobertura de tests E2E + integración confirmada.
- Pipelines QA, TRADING, ANALYTICS, SECURITY_AUDIT: estructura creada, calidad de `run()` por verificar.
- Deuda técnica activa: smoke tests incompletos, sin rate limiting en MCPs, GitAgent stub, Dashboard UI sin verificar.

**Sub-agentes colaboradores propuestos por pipeline (ver ARCHITECTURE.md § Sub-agentes):**
- DEV: `RefactorAnalyzer` (nuevo agente) + `TestValidatorAgent` (nuevo agente) + `GitConfirmAgent` (lógica interna)
- RESEARCH: `SourceValidatorAgent` (nuevo agente) + `BiasDetectorAgent` (lógica interna)
- QA: `RegressionAgent` (nuevo agente) + `ReportFormatterAgent` (nuevo agente)
- TRADING: `DataEnricherAgent` (nuevo agente) + `ScenarioSimulatorAgent` (lógica interna)
- ANALYTICS: `DataValidatorAgent` (nuevo agente) + `TrendComparatorAgent` (lógica interna)
- SECURITY_AUDIT: `AttackSurfaceMapperAgent` (nuevo agente) + `RemediationAdvisorAgent` (nuevo agente)

**Criterio de implementación de sub-agentes:**
> ¿Quieres medir, testear o reusar ese colaborador por separado? Si sí → agente nuevo en el pipeline.
> Si no → lógica interna del agente existente. Implementar en Fase 17-B.

---

## 🟠 Fase 14: Blindar el sistema con tests

> Objetivo: v2.4.0 · Estimado: 3–4 días ← **SIGUIENTE**

### Smoke tests críticos (1/5 completado)
- [x] `tests/smoke/test_mcp_context.py` — MCPHub + AgentContext (CI activo)
- [ ] `test_pipeline_classification` — cada tipo de tarea va al pipeline correcto
- [ ] `test_loop_controller_retry` — fallo de agente activa reintento correcto
- [ ] `test_mcp_hub_fallback` — MCP caído no rompe el agente
- [ ] `test_supabase_persistence` — sesión se guarda y recupera correctamente
- [ ] `test_api_router_fallback` — Groq caído → fallback a Gemini automático

### Rate limiting en MCPHub
- [ ] Brave Search: max 2,000 req/mes en free tier → throttle a 1 req/seg
- [ ] CoinGecko: max 30 req/min → throttle con token bucket
- [ ] OKX: throttle alineado con límites de API key
- [ ] Implementar en `infrastructure/mcp_hub.py` como decorator opcional por MCP

### CI/CD básico (parcial)
- [x] `.github/workflows/ci.yml` — smoke tests en cada push a main y feat/**
- [ ] `.github/workflows/lint.yml` — ruff en cada push

### Verificación de calidad de agentes secundarios (post-14)
> Resultado de auditoría: los pipelines QA, TRADING, ANALYTICS y SECURITY_AUDIT
> tienen estructura creada pero la calidad de `run()` no ha sido auditada recientemente.
- [ ] Auditar `agents/qa/` — verificar uso de MCPHub, sanitizer, sandbox, logging
- [ ] Auditar `agents/security_audit/` — verificar ThreatModeler, CodeReviewer, ComplianceChecker
- [ ] Auditar `agents/analytics/` — verificar DataCollector, InsightGenerator
- [ ] Auditar `agents/trading/` — verificar BacktestReader, MetricsCalculator, RiskAnalyzer, StrategyAdvisor

---

## 🟠 Fase 15: Dashboard UI funcional

> Objetivo: v2.5.0 · Estimado: 1 semana

- [ ] Verificar estado actual de `ui/server.py` y `ui/index.html`
- [ ] Vista de sesiones en tiempo real desde Supabase
- [ ] Gráfica de tokens/costo por pipeline
- [ ] Log de errores de MCPs en tiempo real
- [ ] WebSocket para estado de agentes durante ejecución
- [ ] Panel de MCPs disponibles y su estado de configuración
- [ ] Métricas específicas por pipeline crítico:
  - DEV: tiempo por fase, archivos tocados, reintentos
  - RESEARCH: fuentes utilizadas, latencia, ratio errores MCP
  - TRADING: equity curve, drawdown por estrategia/bot
  - ANALYTICS: consultas Supabase, reportes enviados, errores Slack
  - QA: findings por severidad OWASP, tiempo de auditoría
  - SECURITY_AUDIT: amenazas mapeadas, gaps de compliance

---

## 🔴 Fase 16: Autonomía y Loop de Corrección

> Objetivo: v3.0.0

- [ ] **Worker lifecycle state machine** — `infrastructure/worker_lifecycle.py`
  - [ ] Estados: `spawning → ready → running → blocked → failed → finished`
  - [ ] `failure_kind`: `compile | test | tool_runtime | provider | timeout`
- [ ] **Loop de corrección autónomo** — `core/loop_controller.py`
  - [ ] Detectar error de compilación → inyectar contexto → reintentar
  - [ ] Detectar test failure → inyectar output → reintentar
  - [ ] Máximo `MAX_ITERATIONS=5` por tarea
- [ ] **Hooks de lifecycle** — `infrastructure/hooks/`
  - [ ] `session-start.py`, `user-prompt-submit.py`, `pretool-guard.py`
  - [ ] `posttool-validate.py`, `stop-enforcer.py`
- [ ] **ExecutionMode** — `PLAN_ONLY | SUPERVISED | AUTONOMOUS`
  - [ ] `--plan` = solo genera plan sin ejecutar
  - [ ] `--auto` = ejecuta sin confirmaciones
- [ ] **Effort level** — `min | normal | max` en `TaskPacket`
- [ ] **Thinking habilitado** — chain-of-thought por nivel de effort
- [ ] **Caché de respuestas LLM** — reduce tokens en pipelines largos (deuda técnica)

---

## 🔴 Fase 17: Skills System + Sub-agentes + Comprensión Real del Codebase

> Objetivo: v3.1.0

### 17-A: Skills system v1 ← **DISEÑADO, PENDIENTE IMPLEMENTAR**

El sistema de skills es una capa declarativa (archivos `.md`) que define cómo
cada pipeline debe usar sus agentes para resolver tipos de tareas recurrentes.
**No es código Python** — es contrato de diseño que guía al orquestador.

#### Plan de implementación de skills v1

| Paso | Acción | Archivos afectados | Notas |
|---|---|---|---|
| 1 | Crear `skills/shared/schema.md` | `skills/shared/schema.md` | Formato canónico + ejemplos |
| 2 | Crear `skills/shared/safety_guards.md` | `skills/shared/safety_guards.md` | Reglas globales reutilizables |
| 3 | Crear `claude.md` para los 11 pipelines | `skills/*/claude.md` | Empezar por DEV, RESEARCH, QA |
| 4 | Crear skills core (≥3 por pipeline) | `skills/*/skills/*.md` | Priorizar flujos más frecuentes |
| 5 | Integrar cargador en Maestro | `core/maestro.py` | Solo lectura de `.md`, sin lógica nueva |
| 6 | Tests de validación de skills | `tests/test_skills_schema.py` | Verificar frontmatter y campos obligatorios |
| 7 | Skills de trading (v2) | `skills/trading/` | Después de validar v1 con los 11 pipelines |

**Prioridad de pipelines para skills v1:** DEV → RESEARCH → QA → ANALYTICS → SECURITY_AUDIT → resto.

> **Criterio de done para Fase 17-A:** `skills/shared/schema.md` existe,
> los 11 `claude.md` están escritos, cada pipeline tiene ≥3 skills documentadas,
> y `pytest tests/test_skills_schema.py` pasa en CI.

### 17-B: Sub-agentes colaboradores + GitAgent real

> Resultado de la auditoría de Abril 2026. Implementar los sub-agentes propuestos
> para los 6 pipelines críticos (ver ARCHITECTURE.md § Sub-agentes y colaboradores).

#### Sub-agentes nuevos por pipeline (nuevo agente en el pipeline)

| Sub-agente | Pipeline | Función | Prioridad |
|---|---|---|---|
| `SourceValidatorAgent` | RESEARCH | Valida calidad y credibilidad de fuentes | 🔴 Alta |
| `DataValidatorAgent` | ANALYTICS | Valida integridad de datos antes del análisis | 🔴 Alta |
| `RemediationAdvisorAgent` | SECURITY_AUDIT | Genera tickets de remediación por finding | 🔴 Alta |
| `AttackSurfaceMapperAgent` | SECURITY_AUDIT | Mapea superficie de ataque antes del code review | 🟡 Media |
| `ReportFormatterAgent` | QA | Consolida findings en reporte estructurado OWASP | 🟡 Media |
| `RegressionAgent` | QA | Verifica que bugs encontrados no rompen tests existentes | 🟡 Media |
| `RefactorAnalyzer` | DEV | Analiza codebase antes de codear: módulos afectados, riesgo | 🟡 Media |
| `TestValidatorAgent` | DEV | Valida tests mínimos antes de pasar a ReviewerAgent | 🟡 Media |
| `DataEnricherAgent` | TRADING | Enriquece backtests con datos on-chain y noticias | 🟢 Baja |

#### Lógica interna a añadir en agentes existentes

| Mejora | Agente | Pipeline | Función |
|---|---|---|---|
| `GitConfirmAgent` logic | `git_agent.py` | DEV | Confirma antes de push a main; crea feat/* automáticamente |
| `BiasDetectorAgent` logic | `analyst_agent.py` | RESEARCH | Detecta sesgo en síntesis: fuentes unilaterales |
| `ScenarioSimulatorAgent` logic | `risk_analyzer.py` | TRADING | Simula bull/bear/black swan sobre la estrategia |
| `TrendComparatorAgent` logic | `insight_generator.py` | ANALYTICS | Compara KPIs actuales vs período anterior |

#### Otros ítems de 17-B

- [ ] **Project initializer** — genera `CLAW.md` al escanear workspace
- [ ] **Codebase indexer** — AST Python, búsqueda semántica local
- [ ] **Prompt parser** — `@archivo.py` inyecta contenido automáticamente
- [ ] **File editor tool** — `read_file`, `write_file`, `patch_file` (diff-based)
- [ ] **Session store** — `checkpoint()`, `rewind()`, `resume()`
- [ ] **LSP bridge básico** — diagnósticos vía `pylsp`
- [ ] **Stdin pipe** — `cat archivo.py | python main.py --type review --stdin`
- [ ] **GitAgent real** — conectar `git_ops.py` como agente activo con github_mcp

---

## 🔴 Fase 18: Memoria Episódica

- [ ] **EpisodicMemory** — embeddings locales con `sentence-transformers`
- [ ] `recall_similar(task, top_k=3)` — recupera experiencias parecidas
- [ ] **Meta-skill** — auto-genera skills desde patrones recurrentes
- [ ] **pgvector en Supabase** — reemplaza búsqueda keyword por semántica
- [ ] **Export training data** — dataset JSONL para fine-tuning

---

## 🔴 Fase 19: Docker, Producción y Fine-Tuning

> Requiere GPU dedicada (RTX 3070+)

- [ ] Docker sandbox por tarea (container efímero)
- [ ] CI/CD completo — test + lint + release automático
- [ ] Auth en `/api/task` — JWT
- [ ] Fly.io deploy config
- [ ] SQLite → Supabase como memoria principal
- [ ] Fine-tuning con datos propios (Unsloth + GGUF → Ollama)

---

## 🐛 Deuda técnica activa

| Ítem | Severidad | Fase objetivo | Notas |
|---|---|---|---|
| Smoke tests incompletos | 🔴 Alta | Fase 14 | `test_mcp_context` + CI listos; faltan 4 smoke tests adicionales |
| Sin rate limiting en MCPs | 🟡 Media | Fase 14 | Brave/CoinGecko/OKX con límites de free tier |
| Dashboard UI — estado sin verificar | 🟡 Media | Fase 15 | Verificar `ui/server.py` + `ui/index.html` antes de marcar completo |
| GitAgent es stub funcional | 🟡 Media | Fase 17-B | `git_ops.py` existe; falta agente real conectado |
| Sin lint CI | 🟢 Baja | Fase 14 | Solo hay smoke tests; ruff sin workflow |
| Skills system no implementado | 🟡 Media | Fase 17-A | Diseño completo en ROADMAP; pendiente crear archivos `skills/` |
| MemoryManager usa keywords SQL | 🟢 Baja | Fase 18 | Upgrade a pgvector pendiente |
| Sin caché de respuestas LLM | 🟢 Baja | Fase 16 | Ahorra tokens en pipelines largos |
| Docker sandbox real | 🟡 Media | Fase 19 | Sandbox actual es filesystem only |
| Stubs tombstone en agents/ raíz | 🟢 Baja | Fase 17 cleanup | Son alias de compatibilidad; eliminar en v3 |
| Trading sin skills declarativas | 🟢 Baja | Fase 17-A v2 | Excluido del v1 de skills por diseño; se incorpora después |
| Calidad de run() sin auditar (QA/TRADING/ANALYTICS/SECURITY_AUDIT) | 🟡 Media | Fase 14-post | Estructura creada; implementación real por verificar |
| Sub-agentes colaboradores no implementados | 🟡 Media | Fase 17-B | Diseñados en auditoría Abril 2026; pendiente implementación |
| Contratos de datos DataCollector/InsightGenerator sin documentar | 🟢 Baja | Fase 15 | Riesgo de coupling implícito en ANALYTICS |
| Tests numéricos de TRADING sin cobertura | 🟢 Baja | Fase 17-B | Sharpe, drawdown, win rate sin tests fijos de regresión |

---

## Upgrade path GPU (sin cambios de código)

```env
# RTX 3070 / RX 6700 XT (8 GB VRAM)
OLLAMA_HW_PROFILE=gpu_8gb
LOCAL_GPU_LAYERS=33

# RTX 4070 / RX 7900 (12-16 GB VRAM)
OLLAMA_HW_PROFILE=gpu_16gb
LOCAL_GPU_LAYERS=43
LOCAL_CONTEXT_SIZE=65536

# RTX 4090 / RX 7900 XTX (24 GB VRAM)
OLLAMA_HW_PROFILE=gpu_24gb
LOCAL_GPU_LAYERS=65
LOCAL_CONTEXT_SIZE=128000
```

---

## Timeline visual

```
Abril 2026             Mayo 2026          Junio 2026
────────────────────   ───────────────    ──────────────────
✅ Fase 12 DONE        Fase 14 + 15       Fases 16 + 17-A
✅ Fase 13 DONE    →  Tests + Dashboard  Autonomía + Skills
✅ Auditoría v2.3.1    (2 semanas)        (1 mes)
🟠 Fase 14 NEXT
   Tests + Rate limit
   (esta semana)

                                           Q3 2026
                                           ────────────────────
                                           Fases 17-B + 18 + 19
                                           Sub-agentes + Codebase + Memoria + Producción
                                           (GPU requerida)
```
