# ROADMAP — CLAW Agent System

## Estado actual: v2.2.2

> Última actualización: Abril 8, 2026

---

## ✅ Fases completadas (v1.0.0 → v2.2.2)

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

---

## 🟠 Fase 13: Implementar los 5 agentes core reales — EN PROGRESO (3/5)

> Objetivo: v2.3.0 · Estimado: completar semana del 14 Abril 2026
> Con estos 5 agentes funcionando, el 80% de las tareas tienen respuesta real.

| # | Agente | Pipeline | MCPs que usa | Estado |
|---|---|---|---|---|
| 1 | **WebScoutAgent** | research | brave_search + mcp_memory | ✅ Completado (v2) |
| 2 | **PlannerAgent** | dev + todos | sequential_thinking + mcp_memory | ✅ Completado (v2) |
| 3 | **DataAgent** | trading | coingecko + okx + supabase_mcp | ✅ Completado (v2) |
| 4 | **CoderAgent** | dev | context7 + github_mcp | 🔴 Pendiente |
| 5 | **ReportDistributorAgent** | analytics | supabase_mcp + slack | 🔴 Pendiente |

- [x] Implementar `WebScoutAgent` real con brave_search + fallback DuckDuckGo
- [x] Implementar `PlannerAgent` real con sequential_thinking + memoria episódica
- [x] Implementar `DataAgent` real con coingecko + supabase_mcp
- [ ] Implementar `CoderAgent` real con context7 + github_mcp
- [ ] Implementar `ReportDistributorAgent` real con supabase_mcp + slack

---

## 🟠 Fase 14: Blindar el sistema con tests

> Objetivo: v2.4.0 · Estimado: 3–4 días

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
- [ ] Implementar en `infrastructure/mcp_hub.py` como decorator opcional por MCP

### CI/CD básico (parcial)
- [x] `.github/workflows/ci.yml` — smoke tests en cada push a main y feat/**
- [ ] `.github/workflows/lint.yml` — ruff en cada push

---

## 🟠 Fase 15: Dashboard UI funcional

> Objetivo: v2.5.0 · Estimado: 1 semana

- [ ] Verificar estado actual de `ui/server.py` y `ui/index.html`
- [ ] Vista de sesiones en tiempo real desde Supabase
- [ ] Gráfica de tokens/costo por pipeline
- [ ] Log de errores de MCPs en tiempo real
- [ ] WebSocket para estado de agentes durante ejecución
- [ ] Panel de MCPs disponibles y su estado de configuración

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

---

## 🔴 Fase 17: Comprensión Real del Codebase

- [ ] **Project initializer** — genera `CLAW.md` al escanear workspace
- [ ] **Codebase indexer** — AST Python, búsqueda semántica local
- [ ] **Skills system** — `.claw/skills/<nombre>/SKILL.md` con frontmatter YAML
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
| Sin rate limiting en MCPs | 🟡 Media | Fase 14 | Brave/CoinGecko con límites de free tier |
| Dashboard UI — estado sin verificar | 🟡 Media | Fase 15 | Verificar `ui/server.py` + `ui/index.html` antes de marcar completo |
| CoderAgent usa LLM puro sin context7 | 🟡 Media | Fase 13 | Pendiente último paso de Fase 13 |
| ReportDistributor sin slack MCP | 🟡 Media | Fase 13 | Pendiente último paso de Fase 13 |
| GitAgent es stub funcional | 🟡 Media | Fase 17 | `git_ops.py` existe; falta agente real conectado |
| Sin lint CI | 🟢 Baja | Fase 14 | Solo hay smoke tests; ruff sin workflow |
| MemoryManager usa keywords SQL | 🟢 Baja | Fase 18 | Upgrade a pgvector pendiente |
| Sin caché de respuestas LLM | 🟢 Baja | Fase 16 | Ahorra tokens en pipelines largos |
| Docker sandbox real | 🟡 Media | Fase 19 | Sandbox actual es filesystem only |
| Stubs tombstone en agents/ raíz | 🟢 Baja | Fase 17 cleanup | Son alias de compatibilidad; eliminar en v3 |

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
✅ Fase 12 DONE        Fase 14 + 15       Fases 16 + 17
🟠 Fase 13 (3/5)   →  Tests + Dashboard  Autonomía + Codebase
   CoderAgent +        (2 semanas)        (1 mes)
   ReportDistributor
   (esta semana)

                                           Q3 2026
                                           ────────────────────
                                           Fases 18 + 19
                                           Memoria + Producción
                                           (GPU requerida)
```
