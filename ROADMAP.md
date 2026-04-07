# ROADMAP — CLAW Agent System

## Estado actual: v2.1.0 — Local-first LLM + GPU-ready

> Última actualización: Abril 2026

---

## ✅ Fases completadas (v1.0.0 — v2.0.0)

### Fase 1: DEV Pipeline
- [x] `agents/dev/planner_agent.py`
- [x] `agents/dev/coder_agent.py`
- [x] `agents/dev/reviewer_agent.py`
- [x] `agents/dev/security_agent.py`
- [x] `agents/dev/executor_agent.py`
- [x] `agents/dev/git_agent.py`

### Fase 2: Research, Content y Office
- [x] `agents/research/` — 4 agentes
- [x] `agents/content_agent.py`
- [x] `agents/office_agent.py`

### Fase 3: QA, Trading y PM
- [x] `agents/qa_agent.py`
- [x] `agents/trading_agent.py`
- [x] `agents/pm_agent.py`

### Fase 4-7: Infrastructure, Tools, UI, Docs
- [x] `infrastructure/` — 7 módulos
- [x] `tools/` — 7 tools
- [x] `ui/server.py` + `ui/index.html`
- [x] `README.md`, `ARCHITECTURE.md`, `CONTRIBUTING.md`
- [x] `examples/` — 12 ejemplos

### Fase 8: Sub-pipelines reales
- [x] CONTENT (5), QA (5), PM (4), OFFICE (3), TRADING (4)

### Fase 9: 5 pipelines nuevos
- [x] ANALYTICS (3), MARKETING (4), PRODUCT (4), SECURITY_AUDIT (3), DESIGN (5)
- [x] Clasificador expandido a 12 pipelines en `core/maestro.py`

### Fase 10: Observabilidad y tests E2E
- [x] Tracing automático en `BaseAgent` + `audit_logger.py`
- [x] Input sanitizer (3 capas, 13 patrones) en `infrastructure/input_sanitizer.py`
- [x] 12 tests E2E con mock LLM en `tests/test_e2e_pipelines.py`
- [x] Dashboard métricas en `GET /api/metrics`

---

## ✅ Fase 11 (v2.1.0): LLM Local-First + GPU-Ready

> Completada: Abril 2026

- [x] **`core/api_router.py`** — estrategia `local_first` con 4 providers
  - [x] Ollama como provider primario (gratis, offline)
  - [x] Perfiles de hardware: `cpu_24gb` → `gpu_8gb` → `gpu_24gb`
  - [x] Auto-escalado a cloud cuando contexto local se satura
  - [x] Offload parcial a iGPU Vega 3 (`LOCAL_GPU_LAYERS=4`)
  - [x] `status()` para `/doctor` y `/api/metrics`
- [x] **`.env.example`** — sección Ollama completa con perfiles de hardware
- [x] **`ROADMAP.md`** — fases 12-15 con hitos GPU

### Modelo activo (Athlon 3000G + 24 GB RAM)
```
Provider primario : Ollama local (qwen2.5-coder:7b-q4_K_M)
Velocidad         : ~4-7 tok/s en CPU
Contexto          : 32,768 tokens
iGPU offload      : 4 capas → Vega 3 (+10-20% velocidad)
Fallback 1        : Groq llama-3.3-70b (gratis, 14,400 tok/min)
Fallback 2        : Gemini 2.0 Flash (gratis, 1M tok/día)
Fallback 3        : Hyperspace legacy
```

### Upgrade path — sin cambios de código
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

## 🟠 Fase 12: Autonomía y Loop de Corrección

> Siguiente fase — objetivo: v2.2.0

- [ ] **Worker lifecycle state machine** — `infrastructure/worker_lifecycle.py`
  - [ ] Estados: `spawning → ready → running → blocked → failed → finished`
  - [ ] `failure_kind`: `compile | test | tool_runtime | provider | timeout`
  - [ ] Auto-recovery: 1 intento automático antes de escalar
- [ ] **Loop de corrección autónomo** — `core/loop_controller.py`
  - [ ] Detectar error de compilación → inyectar contexto del error → reintentar
  - [ ] Detectar test failure → inyectar output de tests → reintentar
  - [ ] Máximo `MAX_ITERATIONS=5` por tarea
- [ ] **Typed task packets** — `core/task_packet.py`
  - [ ] `TaskPacket(objective, scope, pipeline, branch_policy, acceptance_tests, escalation_policy)`
  - [ ] Reemplaza strings planos en CLI y `/api/task`
- [ ] **Lane events tipados** — `infrastructure/lane_events.py`
  - [ ] `LaneEvent` enum: `started | blocked | red | green | failed | finished`
  - [ ] Reemplaza logs de texto en `audit_logger.py`
  - [ ] WebSocket del dashboard consume eventos tipados
- [ ] **Tests loop controller** — `tests/test_loop_controller.py`

---

## 🟠 Fase 13: Comprensión Real del Codebase

> Objetivo: que el pipeline DEV lea y edite proyectos existentes

- [ ] **Codebase indexer** — `tools/codebase_indexer.py`
  - [ ] Indexación AST de Python (funciones, clases, imports, docstrings)
  - [ ] Búsqueda semántica sobre el índice local (sin API)
  - [ ] `get_context_for_task(task, top_k=10)` → archivos relevantes
- [ ] **File editor tool** — `tools/file_editor.py`
  - [ ] `read_file`, `write_file`, `patch_file` (diff-based)
  - [ ] Workspace boundary enforcement
  - [ ] Integrado en pipeline DEV como herramienta del `coder_agent`
- [ ] **LSP bridge básico** — `tools/lsp_bridge.py`
  - [ ] Diagnósticos vía `pylsp` (errores, warnings)
  - [ ] Símbolos y definiciones del workspace
  - [ ] Hover info para completación de código
- [ ] **Session store persistente** — `tools/session_store.py`
  - [ ] Guarda estado del workspace entre sesiones
  - [ ] Retoma trabajo interrumpido (`--resume`)

---

## 🟠 Fase 14: Memoria Episódica (Aprendizaje Real)

> El sistema recuerda qué funcionó y qué no

- [ ] **EpisodicMemory** — `infrastructure/episodic_memory.py`
  - [ ] `record_interaction(task, pipeline, result, success)`
  - [ ] Embeddings locales con `sentence-transformers/all-MiniLM-L6-v2` (sin API)
  - [ ] `recall_similar(task, top_k=3)` — recupera experiencias parecidas
  - [ ] `inject_into_context(task, agent_context)` — inyecta memorias al Maestro
  - [ ] Backend configurable: SQLite (default) → ChromaDB → Supabase
- [ ] **Self-improvement export** — `tools/export_training_data.py`
  - [ ] Exporta interacciones exitosas como dataset JSONL
  - [ ] Filtro por `min_success_score` (configurable en `.env`)
  - [ ] Formato compatible con Unsloth para fine-tuning posterior
- [ ] **Tests memoria episódica** — `tests/test_episodic_memory.py`

---

## 🔴 Fase 15: Docker, Producción y Fine-Tuning

> Requiere GPU dedicada (RTX 3070+)

- [ ] **Docker sandbox por tarea** — `infrastructure/docker_sandbox.py`
  - [ ] Container efímero por ejecución del pipeline DEV
  - [ ] Capability probe: Docker → unshare namespace → process isolation
  - [ ] `docker-compose.yml` para deploy completo
- [ ] **Fine-tuning con datos propios** (requiere 8+ GB VRAM)
  - [ ] Script de entrenamiento con Unsloth: `tools/finetune.py`
  - [ ] Input: dataset de `export_training_data.py` (~500+ sesiones exitosas)
  - [ ] Output: modelo GGUF importable en Ollama
  - [ ] Convierte `qwen2.5-coder:7b` en un modelo especializado en TU codebase
- [ ] **CI/CD completo** — `.github/workflows/`
  - [ ] `test.yml` — pytest en cada PR
  - [ ] `lint.yml` — ruff + mypy
  - [ ] `release.yml` — tag → changelog automático
- [ ] **Auth en `/api/task`** — token o sesión JWT
- [ ] **Fly.io deploy config** — `fly.toml`
- [ ] **Supabase como memoria principal** (migrar desde SQLite)
- [ ] **API pública con rate limiting** para SaaS

---

## Deuda técnica activa

| Ítem | Severidad | Fase objetivo |
|------|-----------|---------------|
| Worker lifecycle state machine | Alta | Fase 12 |
| Loop de corrección autónomo | Alta | Fase 12 |
| Codebase indexer (AST) | Alta | Fase 13 |
| Memoria episódica | Media | Fase 14 |
| Docker sandbox real | Media | Fase 15 |
| SQLite → Supabase principal | Media | Fase 15 |
| Auth en `/api/task` | Media | Fase 15 |
| Fine-tuning con datos propios | Media | Fase 15 (GPU) |
| GitAgent stub → real | Media | Fase 13 |
| asyncio.gather generalizado | Baja | Fase 12 |
| LSP bridge básico | Baja | Fase 13 |

---

## Setup rápido (v2.1.0)

```bash
# 1. Instalar Ollama (Windows)
winget install Ollama.Ollama

# 2. Bajar modelo óptimo para Athlon 3000G + 24 GB RAM
ollama pull qwen2.5-coder:7b-q4_K_M

# 3. Configurar variables de entorno
cp .env.example .env
# Editar .env — mínimo:
#   OLLAMA_ENABLED=true
#   OLLAMA_HW_PROFILE=cpu_24gb
#   GROQ_API_KEY=tu_key   ← https://console.groq.com (gratis)

# 4. Verificar sistema
python main.py --doctor

# 5. Primera tarea con LLM local
python main.py --task "Crea una API REST para señales de trading" --type dev
```

## CLI disponible

```bash
python main.py --task "<tarea>" --type <pipeline>
python main.py --interactive          # Loop de tareas
python main.py --ui                   # Dashboard → http://127.0.0.1:8000
python main.py --doctor               # Diagnóstico + estado del router LLM
python main.py --history              # Últimas 20 sesiones
python main.py --usage                # Tokens y costos acumulados
```

## Pipelines disponibles (v2.1.0)

| Pipeline | Flag | Agentes | Provider primario |
|----------|------|---------|------------------|
| DEV | `--type dev` | 6 | Ollama local |
| RESEARCH | `--type research` | 4 | Groq (cloud) |
| CONTENT | `--type content` | 5 | Ollama local |
| OFFICE | `--type office` | 3 | Ollama local |
| QA | `--type qa` | 5 | Ollama local |
| TRADING | `--type trading` | 4 | Ollama local |
| PM | `--type pm` | 4 | Ollama local |
| ANALYTICS | `--type analytics` | 3 | Ollama local |
| MARKETING | `--type marketing` | 4 | Ollama local |
| PRODUCT | `--type product` | 4 | Ollama local |
| SECURITY_AUDIT | `--type security_audit` | 3 | Groq (cloud) |
| DESIGN | `--type design` | 5 | Ollama local |
