# ROADMAP — CLAW Agent System

## Estado actual: v2.1.0

> Última actualización: Abril 7, 2026

---

## ✅ Fases completadas (v1.0.0 → v2.1.0)

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

---

## 🟠 Fase 12: Activar lo que ya existe `← SIGUIENTE`

> Objetivo: v2.2.0 · Estimado: 1 semana
> **El trabajo pesado ya está hecho. Solo hay que conectar piezas y llenar stubs.**

### Paso 1 — Conectar MCPHub a AgentContext `[CRÍTICO]`
- [ ] Agregar `self.mcp = get_mcp_hub()` en `core/context.py`
- [ ] Verificar que todos los agentes pueden acceder `ctx.mcp.call("mcp_name", "tool", {...})`
- [ ] Test: `ctx.mcp.available()` retorna lista de MCPs listos

### Paso 2 — Resolver duplicidad de agentes
- [ ] Eliminar stubs en raíz que duplican sub-agentes en directorio:
  - `agents/trading_agent.py` → reemplazar por `agents/trading/__init__.py`
  - `agents/qa_agent.py` → reemplazar por `agents/qa/__init__.py`
  - `agents/content_agent.py` → reemplazar por `agents/content/__init__.py`
  - `agents/pm_agent.py` → reemplazar por `agents/pm/__init__.py`
  - `agents/office_agent.py` → reemplazar por `agents/office/__init__.py`
  - `agents/doc_agent.py` → evaluar si es necesario o redundante
- [ ] Verificar que `core/maestro.py` importa desde los directorios correctos

### Paso 3 — Limpiar archivos redundantes
- [ ] Evaluar `core/orchestrator.py` — redundante con `Maestro`; eliminar o documentar
- [ ] Evaluar `core/pipeline.py` — redundante con `PipelineRouter`; eliminar o documentar
- [ ] Actualizar imports en archivos que los referencien

### Paso 4 — Conectar mcp_memory en BaseAgent
- [ ] `base_agent.py` → al inicio de `run()`: recuperar contexto previo de `mcp_memory`
- [ ] `base_agent.py` → al final de `run()`: guardar conclusiones en `mcp_memory`
- [ ] Un solo cambio → todos los agentes heredan memoria persistente automáticamente

### Paso 5 — Conectar sequential_thinking en PlannerAgent
- [ ] `agents/dev/planner_agent.py` → llamar `ctx.mcp.call("sequential_thinking", "decompose", {...})` antes de planificar
- [ ] No requiere API key — funciona ahora mismo

---

## 🟠 Fase 13: Implementar los 5 agentes core reales

> Objetivo: v2.3.0 · Estimado: 1 semana
> Con estos 5 agentes funcionando, el 80% de las tareas tienen respuesta real.

| # | Agente | Pipeline | MCPs que usa | Responsabilidad |
|---|---|---|---|---|
| 1 | **WebScoutAgent** | research | brave_search + mcp_memory | Busca, filtra duplicados, sintetiza informe |
| 2 | **PlannerAgent** | dev + todos | sequential_thinking + mcp_memory | Descompone tareas en subtareas con dependencias |
| 3 | **CoderAgent** | dev | context7 + github_mcp | Genera/revisa código con docs actualizadas |
| 4 | **DataAgent** | trading | coingecko + okx + supabase_mcp | Recopila datos de mercado, guarda en Supabase |
| 5 | **ReportDistributorAgent** | analytics | supabase_mcp + slack | Lee métricas, envía reporte formateado |

- [ ] Implementar `WebScoutAgent` real con brave_search
- [ ] Implementar `PlannerAgent` real con sequential_thinking
- [ ] Implementar `CoderAgent` real con context7 + github_mcp
- [ ] Implementar `DataAgent` real con coingecko + supabase_mcp
- [ ] Implementar `ReportDistributorAgent` real con supabase_mcp + slack

---

## 🟠 Fase 14: Blindar el sistema con tests

> Objetivo: v2.4.0 · Estimado: 3–4 días

### 5 smoke tests críticos
- [ ] `test_pipeline_classification` — cada tipo de tarea va al pipeline correcto
- [ ] `test_loop_controller_retry` — fallo de agente activa reintento correcto
- [ ] `test_mcp_hub_fallback` — MCP caído no rompe el agente
- [ ] `test_supabase_persistence` — sesión se guarda y recupera correctamente
- [ ] `test_api_router_fallback` — Groq caído → fallback a Gemini automático

### Rate limiting en MCPHub
- [ ] Brave Search: max 2,000 req/mes en free tier → throttle a 1 req/seg
- [ ] CoinGecko: max 30 req/min → throttle con token bucket
- [ ] Implementar en `infrastructure/mcp_hub.py` como decorator opcional por MCP

### CI/CD básico
- [ ] `.github/workflows/test.yml` — pytest en cada PR
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
| MCPHub no conectado a AgentContext | 🔴 Crítica | Fase 12 - Paso 1 | Una línea en context.py |
| Stubs duplicados en agents/ raíz | 🔴 Alta | Fase 12 - Paso 2 | 6 archivos a eliminar/fusionar |
| orchestrator.py redundante | 🟡 Media | Fase 12 - Paso 3 | Evaluar antes de eliminar |
| pipeline.py redundante | 🟡 Media | Fase 12 - Paso 3 | Evaluar antes de eliminar |
| mcp_memory no conectado a BaseAgent | 🔴 Alta | Fase 12 - Paso 4 | Memoria persistente para todos |
| sequential_thinking no usado | 🔴 Alta | Fase 12 - Paso 5 | PlannerAgent sin reasoning real |
| Sin smoke tests críticos | 🔴 Alta | Fase 14 | Sistema sin red de seguridad |
| Sin rate limiting en MCPs | 🟡 Media | Fase 14 | Brave/CoinGecko con límites |
| Dashboard UI — estado desconocido | 🟡 Media | Fase 15 | Verificar antes de completar |
| CLOUD_CONTEXT_LIMITS 1M sin actualizar | 🟢 Baja | Fase 12 fix | api_router.py |
| GitAgent es stub | 🟡 Media | Fase 17 | git_ops.py ya existe como base |
| MemoryManager usa keywords SQL | 🟢 Baja | Fase 18 | Upgrade a pgvector |
| Sin caché de respuestas LLM | 🟢 Baja | Fase 16 | Ahorra tokens en pipelines largos |
| Docker sandbox real | 🟡 Media | Fase 19 | Sandbox actual es filesystem only |

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
Abril 2026          Mayo 2026          Junio 2026
────────────────    ───────────────    ──────────────────
Fase 12 ✦          Fase 14 + 15       Fases 16 + 17
Activar piezas  →  Tests + Dashboard  Autonomía + Codebase
(1 semana)         (2 semanas)        (1 mes)

                                      Q3 2026
                                      ────────────────────
                                      Fases 18 + 19
                                      Memoria + Producción
                                      (GPU requerida)
```
