# ROADMAP — CLAW Agent System

## Estado actual: v2.3.0

> Última actualización: Abril 8, 2026

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

## 🔴 Fase 17: Skills System + Comprensión Real del Codebase

> Objetivo: v3.1.0 · Incluye el sistema de skills declarativas por pipeline

### 17-A: Skills system v1 ← **DISEÑADO, PENDIENTE IMPLEMENTAR**

El sistema de skills es una capa declarativa (archivos `.md`) que define cómo
cada pipeline debe usar sus agentes para resolver tipos de tareas recurrentes.
**No es código Python** — es contrato de diseño que guía al orquestador.

#### Estructura de `skills/`

```text
skills/
  shared/
    schema.md             # Formato estándar y campos obligatorios de una skill
    safety_guards.md      # Reglas globales: no credenciales, no push sin confirmar, etc.

  dev/
    claude.md             # Orquestador conceptual del pipeline DEV
    skills/
      implement_feature.md   # Implementar una feature nueva end-to-end
      code_review.md         # Revisión de código con criterios definidos
      write_tests.md         # Generar suite de tests para un módulo
      refactor_module.md     # Refactorizar sin cambiar comportamiento observable

  research/
    claude.md
    skills/
      web_research.md        # Investigación web con brave_search + síntesis
      competitor_analysis.md # Análisis de competidores con múltiples fuentes
      summarize_sources.md   # Resumir N fuentes en un documento estructurado

  content/
    claude.md
    skills/
      longform_to_social.md  # Convertir contenido largo a posts por red social
      newsletter_issue.md    # Generar un número completo de newsletter
      landing_copy.md        # Copy de landing page con estructura AIDA

  office/
    claude.md
    skills/
      meeting_notes.md       # Procesar grabación/texto → acta + acciones
      task_extraction.md     # Extraer tareas y owners de documentos
      email_reply.md         # Redactar respuestas de email en tono definido

  qa/
    claude.md
    skills/
      static_audit.md        # Auditoría estática con semgrep + checklist OWASP
      test_plan.md           # Plan de pruebas para un módulo o feature
      regression_suite.md    # Suite de regresión con playwright

  pm/
    claude.md
    skills/
      roadmap_from_ideas.md  # Convertir lista de ideas en roadmap priorizado
      sprint_planning.md     # Planning de sprint con estimaciones y dependencias
      backlog_grooming.md    # Grooming de backlog con criterios de aceptación

  analytics/
    claude.md
    skills/
      kpi_report.md          # Reporte semanal/mensual de KPIs con tendencias
      funnel_analysis.md     # Análisis de embudo de conversión
      cohort_analysis.md     # Análisis de retención por cohortes

  marketing/
    claude.md
    skills/
      campaign_brief.md      # Brief completo de campaña: objetivo, audiencia, canales
      audience_persona.md    # Definición de persona con demographics + psicographics
      multi_channel_post.md  # Post optimizado por canal (X, LinkedIn, Instagram, YT, email)
      content_calendar.md    # Calendario editorial mensual con temas y formatos

  product/
    claude.md
    skills/
      problem_interview.md   # Guía de entrevista de problema + análisis de respuestas
      feature_brief.md       # Brief de feature: problema, solución, métricas de éxito
      prioritization_rice.md # Priorización RICE de backlog con justificación

  security_audit/
    claude.md
    skills/
      threat_model.md        # Modelo de amenazas STRIDE para un sistema dado
      code_security_review.md # Revisión de seguridad con semgrep + criterios OWASP Top 10
      compliance_gap.md      # Gap analysis GDPR/CCPA/SOC2

  design/
    claude.md
    skills/
      ui_review.md           # Revisión de UI contra principios de usabilidad
      ux_audit.md            # Auditoría UX con heurísticas de Nielsen
      brand_system.md        # Definición de sistema de marca: colores, tipografía, voz

  # TRADING: excluido del v1 de skills.
  # El pipeline trading mantiene sus agentes actuales (DataAgent, BacktestReader,
  # MetricsCalculator, RiskAnalyzer, StrategyAdvisor) sin skills declarativas.
  # Se incorporará en v2 del sistema de skills cuando la arquitectura esté validada.
```

#### Qué define cada `claude.md`

Cada `skills/<pipeline>/claude.md` especifica:

```md
# <PIPELINE> pipeline — claude.md

Rol: [qué problema resuelve el pipeline y en qué contextos se activa]

Agentes disponibles:
  - <nombre>  → agents/<pipeline>/<nombre>_agent.py — [qué hace]

Skills autorizadas:
  - <nombre_skill>  — [descripción de una línea]

MCPs permitidos para este pipeline:
  - mcp_memory          # siempre disponible (BaseAgent)
  - sequential_thinking # razonamiento estructurado
  - [mcps adicionales según pipeline]

Restricciones de seguridad:
  - [reglas específicas del pipeline: confirmaciones, límites de escritura, etc.]

Política de calidad:
  - [criterios de done para este pipeline]
```

#### Formato de una skill `.md`

Cada `skills/<pipeline>/skills/<nombre>.md` sigue este esquema
(definido canónicamente en `skills/shared/schema.md`):

```md
name: <nombre_corto_snake_case>
pipeline: <pipeline>
version: 1.0.0
last_updated: YYYY-MM-DD

description: |
  Describe en 2–4 frases qué problema resuelve esta skill,
  qué entrega como output y en qué casos debe usarse.

required_inputs:
  - nombre_input: descripción y tipo esperado

optional_inputs:
  - nombre_input: descripción y valor por defecto

agents_involved:
  - AgentName: rol específico en esta skill

tools:
  - mcp_memory
  - [otros MCPs necesarios]

steps:
  1. [Paso de alto nivel]
  2. [Paso de alto nivel]
  ...

output_format: |
  Describe la estructura esperada del output:
  Markdown con secciones X, Y, Z / JSON con campos A, B / etc.

quality_criteria:
  - [Criterio verificable de "done"]

failure_modes:
  - modo: [qué puede salir mal]
    respuesta: [cómo reaccionar]

examples:
  - input: "[ejemplo de tarea que activa esta skill]"
    expected_output: "[descripción del output esperado]"
```

#### Plan de implementación de skills v1

| Paso | Acción | Archivos afectados | Notas |
|---|---|---|---|
| 1 | Crear `skills/shared/schema.md` | `skills/shared/schema.md` | Formato canónico + ejemplos |
| 2 | Crear `skills/shared/safety_guards.md` | `skills/shared/safety_guards.md` | Reglas globales reutilizables |
| 3 | Crear `claude.md` para los 11 pipelines | `skills/*/claude.md` | Empezar por DEV, RESEARCH, MARKETING |
| 4 | Crear skills core (3 por pipeline) | `skills/*/skills/*.md` | Priorizar los flujos más frecuentes |
| 5 | Integrar cargador en Maestro | `core/maestro.py` | Solo lectura de `.md`, sin lógica nueva |
| 6 | Tests de validación de skills | `tests/test_skills_schema.py` | Verificar frontmatter y campos obligatorios |
| 7 | Skills de trading (v2) | `skills/trading/` | Después de validar v1 con los 11 pipelines |

> **Criterio de done para Fase 17-A:** `skills/shared/schema.md` existe,
> los 11 `claude.md` están escritos, cada pipeline tiene ≥3 skills documentadas,
> y `pytest tests/test_skills_schema.py` pasa en CI.

### 17-B: Comprensión Real del Codebase

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
| Sin rate limiting en MCPs | 🟡 Media | Fase 14 | Brave/CoinGecko con límites de free tier |
| Dashboard UI — estado sin verificar | 🟡 Media | Fase 15 | Verificar `ui/server.py` + `ui/index.html` antes de marcar completo |
| GitAgent es stub funcional | 🟡 Media | Fase 17-B | `git_ops.py` existe; falta agente real conectado |
| Sin lint CI | 🟢 Baja | Fase 14 | Solo hay smoke tests; ruff sin workflow |
| Skills system no implementado | 🟡 Media | Fase 17-A | Diseño completo en ROADMAP; pendiente crear archivos `skills/` |
| MemoryManager usa keywords SQL | 🟢 Baja | Fase 18 | Upgrade a pgvector pendiente |
| Sin caché de respuestas LLM | 🟢 Baja | Fase 16 | Ahorra tokens en pipelines largos |
| Docker sandbox real | 🟡 Media | Fase 19 | Sandbox actual es filesystem only |
| Stubs tombstone en agents/ raíz | 🟢 Baja | Fase 17 cleanup | Son alias de compatibilidad; eliminar en v3 |
| Trading sin skills declarativas | 🟢 Baja | Fase 17-A v2 | Excluido del v1 de skills por diseño; se incorpora después |

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
🟠 Fase 14 NEXT        (2 semanas)        (1 mes)
   Tests + Rate limit
   (esta semana)

                                           Q3 2026
                                           ────────────────────
                                           Fases 17-B + 18 + 19
                                           Codebase + Memoria + Producción
                                           (GPU requerida)
```
