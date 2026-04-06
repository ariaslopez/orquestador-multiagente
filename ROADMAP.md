# ROADMAP — CLAW Agent System

## Estado actual: v2.0.0 — 12 pipelines operativos

> Última actualización: Abril 2026

---

## ✅ Fases completadas (v1.0.0)

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

### Fase 4: Infrastructure
- [x] `infrastructure/memory_manager.py`
- [x] `infrastructure/security_layer.py`
- [x] `infrastructure/security_sandbox.py`
- [x] `infrastructure/audit_logger.py`
- [x] `infrastructure/state_manager.py`
- [x] `infrastructure/output_manager.py`

### Fase 5: Tools
- [x] `tools/` — 7 tools

### Fase 6: UI Dashboard
- [x] `ui/server.py` + `ui/index.html`

### Fase 7: Documentación y Ejemplos
- [x] `README.md`, `ROADMAP.md`, `ARCHITECTURE.md`
- [x] `examples/` — 7 ejemplos
- [x] `tests/` — tests unitarios base

---

## ✅ Fase 8: Expandir pipelines macro a sub-pipelines reales

> Completada: Abril 2026

- [x] CONTENT pipeline (5 sub-agentes)
- [x] QA pipeline (5 sub-agentes)
- [x] PM pipeline (4 sub-agentes)
- [x] OFFICE pipeline (3 sub-agentes)
- [x] TRADING pipeline (4 sub-agentes)
- [x] `config.yaml` + `core/maestro.py` actualizados

---

## ✅ Fase 9: 5 pipelines nuevos

> Completada: Abril 2026

- [x] ANALYTICS pipeline (3 agentes)
- [x] MARKETING pipeline (4 agentes)
- [x] PRODUCT pipeline (4 agentes)
- [x] SECURITY_AUDIT pipeline (3 agentes)
- [x] DESIGN pipeline (5 agentes)
- [x] Clasificador expandido a 12 pipelines
- [x] `examples/` con 5 ejemplos nuevos

---

## ✅ Fase 10: Observabilidad y tests E2E

> Completada: Abril 2026

- [x] **Tracing por agente** — `infrastructure/audit_logger.py`
  - [x] `log_agent_trace(agent, pipeline, session_id, duration_ms, tokens, cost_usd)`
  - [x] `get_pipeline_stats()` — agrega métricas por pipeline
  - [x] `get_most_used_pipeline()`
- [x] **Tracing automático en BaseAgent** — `core/base_agent.py`
  - [x] `execute()` captura `time.monotonic()` antes/después de `run()`
  - [x] Calcula delta tokens y costo por agente individual
  - [x] Llama `log_agent_trace()` automáticamente, sin tocar subclases
- [x] **Sanitización prompt injection** — `infrastructure/input_sanitizer.py`
  - [x] 3 capas: jailbreak patterns, system override, structural injection
  - [x] Integrado en `/api/task` y `/ws/task` del servidor
  - [x] Integrado en `Maestro.run()` como primera línea de defensa
- [x] **Fix regresión CI** — `tests/test_pipeline_imports.py`
  - [x] `AGENT_REGISTRY` actualizado a los 52 agentes de 12 pipelines
  - [x] Assert actualizado de 7 → 12 pipelines
- [x] **Tests E2E** — `tests/test_e2e_pipelines.py`
  - [x] 12 tests (uno por pipeline) con mock LLM
  - [x] Valida: `status == completed`, `pipeline_name`, `final_output` no vacío, `total_tokens >= 0`
- [x] **Tests InputSanitizer** — `tests/test_input_sanitizer.py`
  - [x] 12 tests: safe inputs, jailbreak, system override, structural, longitud, assert_safe
- [x] **Dashboard métricas** — `ui/server.py` + `FALLBACK_HTML`
  - [x] Endpoint `GET /api/metrics` con stats por pipeline
  - [x] Panel de observabilidad en UI: calls, tokens, costo, avg_duration_ms, error_rate
  - [x] Selector de 12 pipelines en el formulario

---

## 🟠 Fase 11: Producción y escalabilidad

- [ ] Docker container efímero por tarea (sandboxing real a nivel OS)
- [ ] Docker-compose para deploy en servidor
- [ ] Fly.io deploy config
- [ ] Migrar memoria SQLite → Supabase como fuente principal
- [ ] Autenticación en `/api/task` (token o sesión)
- [ ] Soporte paralelo real con `asyncio.gather` entre agentes

---

## 🔴 Fase 12: Integraciones avanzadas

- [ ] GitAgent real (branch → commit → PR via GitHub API)
- [ ] Integración con crypto-intelligence-hub
- [ ] Plugin Hyperspace como backend LLM local
- [ ] Multi-proyecto: orquestador sobre repos externos
- [ ] API pública con rate limiting para SaaS

---

## Deuda técnica activa

| Ítem | Severidad | Fase objetivo |
|------|-----------|---------------|
| Docker sandbox real | Media | Fase 11 |
| SQLite → Supabase principal | Media | Fase 11 |
| Auth en `/api/task` | Media | Fase 11 |
| GitAgent stub → real | Media | Fase 12 |
| asyncio.gather generalizado | Baja | Fase 11 |
| Hyperspace plugin | Baja | Fase 12 |

---

## Uso rápido

```bash
# Setup
cp .env.example .env && python setup.py

# Verificar sistema
python main.py --doctor

# Ejecutar tarea
python main.py --task "Crea una API REST para señales de trading" --type dev
python main.py --task "Plan de marketing para SaaS B2B" --type marketing
python main.py --task "Audita seguridad de esta API" --type security_audit

# Tests
pytest tests/ -v
pytest tests/test_e2e_pipelines.py -v
pytest tests/test_pipeline_imports.py -v
pytest tests/test_input_sanitizer.py -v

# UI
python main.py --ui  # http://127.0.0.1:8000
```

## Pipelines disponibles (v2.0.0)

| Pipeline | Flag | Agentes |
|----------|------|---------|
| DEV | `--type dev` | 6 |
| RESEARCH | `--type research` | 4 (2 paralelo + 2 secuencial) |
| CONTENT | `--type content` | 5 |
| OFFICE | `--type office` | 3 |
| QA | `--type qa` | 5 |
| TRADING | `--type trading` | 4 |
| PM | `--type pm` | 4 |
| ANALYTICS | `--type analytics` | 3 |
| MARKETING | `--type marketing` | 4 |
| PRODUCT | `--type product` | 4 |
| SECURITY_AUDIT | `--type security_audit` | 3 |
| DESIGN | `--type design` | 5 |
