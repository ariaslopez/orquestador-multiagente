# ROADMAP — CLAW Agent System

## Estado actual: v2.0.0 — 12 pipelines operativos

> Última actualización: Abril 2026

---

## ✅ Fases completadas (v1.0.0)

### Fase 1: DEV Pipeline
- [x] `agents/dev/planner_agent.py` — plan de archivos y stack
- [x] `agents/dev/coder_agent.py` — genera código archivo por archivo
- [x] `agents/dev/reviewer_agent.py` — detecta y corrige bugs
- [x] `agents/dev/security_agent.py` — valida vulnerabilidades
- [x] `agents/dev/executor_agent.py` — escribe en disco, instala deps
- [x] `agents/dev/git_agent.py` — hook Git/GitHub (stub seguro)

### Fase 2: Research, Content y Office
- [x] `agents/research/webscout_agent.py` — búsqueda web DuckDuckGo
- [x] `agents/research/data_agent.py` — datos de mercado CoinGecko/DeFiLlama
- [x] `agents/research/analyst_agent.py` — análisis de datos recopilados
- [x] `agents/research/thesis_agent.py` — tesis de inversión estructurada
- [x] `agents/content_agent.py` — contenido crypto con personalidades LLM
- [x] `agents/office_agent.py` — Excel, PDF, Word, CSV → reportes

### Fase 3: QA, Trading y PM
- [x] `agents/qa_agent.py` — auditoría de código (bugs, seguridad, performance)
- [x] `agents/trading_agent.py` — análisis de bots, backtests, métricas quant
- [x] `agents/pm_agent.py` — backlog, roadmap y sprints desde descripción

### Fase 4: Infrastructure
- [x] `infrastructure/memory_manager.py` — SQLite local + Supabase cloud
- [x] `infrastructure/security_layer.py` — 5 capas de protección
- [x] `infrastructure/security_sandbox.py` — sandbox filesystem y comandos
- [x] `infrastructure/audit_logger.py` — registro completo de operaciones
- [x] `infrastructure/state_manager.py` — estado de sesión
- [x] `infrastructure/output_manager.py` — carpetas de salida

### Fase 5: Tools
- [x] `tools/web_search.py` — DuckDuckGo sin API key
- [x] `tools/safe_filesystem.py` — filesystem auditado
- [x] `tools/file_ops.py` — operaciones de archivos
- [x] `tools/office_reader.py` — lectura Office/PDF
- [x] `tools/code_executor.py` — ejecución segura (shell=False)
- [x] `tools/crypto_data.py` — datos crypto (CoinGecko/DeFiLlama)
- [x] `tools/git_ops.py` — integración GitHub API

### Fase 6: UI Dashboard
- [x] `ui/server.py` — FastAPI + WebSockets
- [x] `ui/index.html` — dashboard Tailwind con selector de pipeline
- [x] Endpoints: `/api/task`, `/api/sessions`, `/api/stats`, `/ws/task`

### Fase 7: Documentación y Ejemplos
- [x] `README.md`, `ROADMAP.md`, `ARCHITECTURE.md`
- [x] `examples/` — 7 ejemplos listos (uno por pipeline)
- [x] Tests unitarios en `tests/`

---

## ✅ Fase 8: Expandir pipelines macro a sub-pipelines reales

> Completada: Abril 2026

- [x] **CONTENT pipeline** (5 sub-agentes)
  - [x] `agents/content/topic_agent.py`
  - [x] `agents/content/writer_agent.py`
  - [x] `agents/content/editor_agent.py`
  - [x] `agents/content/brand_agent.py`
  - [x] `agents/content/scheduler_agent.py`

- [x] **QA pipeline** (5 sub-agentes)
  - [x] `agents/qa/static_analyzer.py`
  - [x] `agents/qa/bug_hunter.py`
  - [x] `agents/qa/security_reviewer.py`
  - [x] `agents/qa/performance_profiler.py`
  - [x] `agents/qa/test_generator.py`

- [x] **PM pipeline** (4 sub-agentes)
  - [x] `agents/pm/requirements_parser.py`
  - [x] `agents/pm/backlog_builder.py`
  - [x] `agents/pm/sprint_planner.py`
  - [x] `agents/pm/roadmap_generator.py`

- [x] **OFFICE pipeline** (3 sub-agentes)
  - [x] `agents/office/file_reader.py`
  - [x] `agents/office/data_analyzer.py`
  - [x] `agents/office/report_writer.py`

- [x] **TRADING pipeline** (4 sub-agentes)
  - [x] `agents/trading/backtest_reader.py`
  - [x] `agents/trading/metrics_calculator.py`
  - [x] `agents/trading/risk_analyzer.py`
  - [x] `agents/trading/strategy_advisor.py`

- [x] `config.yaml` actualizado con los 5 pipelines expandidos
- [x] `core/maestro.py` actualizado con los 5 builders
- [x] `examples/` con ejemplos de todos los pipelines

---

## ✅ Fase 9: 5 pipelines nuevos (ANALYTICS, MARKETING, PRODUCT, SECURITY_AUDIT, DESIGN)

> Completada: Abril 2026

- [x] **ANALYTICS pipeline** (3 agentes)
  - [x] `agents/analytics/data_collector.py` — consolida datos de múltiples fuentes
  - [x] `agents/analytics/insight_generator.py` — extrae insights de negocio
  - [x] `agents/analytics/report_distributor.py` — formatea y distribuye reportes

- [x] **MARKETING pipeline** (4 agentes)
  - [x] `agents/marketing/strategy_agent.py` — estrategia de contenido y canales
  - [x] `agents/marketing/copy_agent.py` — copywriting para landing, ads, emails
  - [x] `agents/marketing/growth_agent.py` — loops de adquisición y pricing
  - [x] `agents/marketing/analytics_agent.py` — métricas de marketing (CAC, LTV)

- [x] **PRODUCT pipeline** (4 agentes)
  - [x] `agents/product/market_researcher.py` — análisis competitivo
  - [x] `agents/product/feedback_synthesizer.py` — síntesis de feedback de usuarios
  - [x] `agents/product/feature_prioritizer.py` — priorización data-driven RICE/MoSCoW
  - [x] `agents/product/nudge_designer.py` — diseño de nudges de comportamiento

- [x] **SECURITY_AUDIT pipeline** (3 agentes)
  - [x] `agents/security/threat_modeler.py` — modelado de amenazas STRIDE
  - [x] `agents/security/code_reviewer.py` — revisión de código OWASP Top 10
  - [x] `agents/security/compliance_checker.py` — GDPR/CCPA/API TOS compliance

- [x] **DESIGN pipeline** (5 agentes)
  - [x] `agents/design/ui_agent.py` — design system y especificaciones de componentes
  - [x] `agents/design/ux_agent.py` — arquitectura de información y user flows
  - [x] `agents/design/brand_agent.py` — naming, identidad visual y brand guidelines
  - [x] `agents/design/a11y_agent.py` — auditoría WCAG 2.1 AA
  - [x] `agents/design/prompt_engineer.py` — prompts para Midjourney/DALL-E/SD

- [x] Clasificador en Maestro expandido a 12 pipelines
- [x] `config.yaml` con los 5 pipelines nuevos
- [x] `examples/` con 5 ejemplos nuevos (analytics, marketing, product, security, design)

---

## 🟡 Fase 10: Observabilidad y tests E2E

- [ ] Tests de integración E2E para cada pipeline (inputs sintéticos → validar shape de contexto)
- [ ] Check de regresión: cada agente en `config.yaml` tiene clase importable
- [ ] Tracing por agente (tiempo, tokens, costo) en `audit_logger.py`
- [ ] Dashboard de métricas en `ui/index.html` (tokens/sesión, pipeline más usado, costos)
- [ ] Alertas de error por pipeline (Slack/webhook opcional)

---

## 🟠 Fase 11: Producción y escalabilidad

- [ ] Docker container efímero por tarea (sandboxing real a nivel OS)
- [ ] Docker-compose para deploy en servidor
- [ ] Fly.io deploy config
- [ ] Migrar memoria SQLite → Supabase como fuente principal
- [ ] Autenticación en `/api/task` (token o sesión)
- [ ] Soporte paralelo real con `asyncio.gather` entre agentes (generalizar más allá de RESEARCH)

---

## 🔴 Fase 12: Integraciones avanzadas

- [ ] Agente GitHubPR real (extiende GitAgent + GitOpsTool: branch → commit → PR)
- [ ] Integración con crypto-intelligence-hub (eventos de mercado → trigger de pipelines)
- [ ] Plugin Hyperspace como backend LLM local (Ollama compatible)
- [ ] Multi-proyecto: orquestador puede trabajar sobre repos externos
- [ ] API pública con rate limiting para uso como SaaS

---

## Deuda técnica activa

| Ítem | Severidad | Fase objetivo |
|------|-----------|---------------|
| Tests E2E por pipeline | Alta | Fase 10 |
| Tracing por agente | Alta | Fase 10 |
| Docker sandbox real | Media | Fase 11 |
| SQLite → Supabase principal | Media | Fase 11 |
| Auth en `/api/task` | Media | Fase 11 |
| GitAgent stub → real | Media | Fase 12 |
| asyncio.gather generalizado | Baja | Fase 11 |
| Hyperspace plugin | Baja | Fase 12 |
| Sanitización de input (prompt injection) | Alta | Fase 10 |

---

## Uso rápido

```bash
# Setup
cp .env.example .env && python setup.py

# Verificar sistema
python main.py --doctor

# Ejecutar tarea
python main.py --task "Crea una API REST para señales de trading" --type dev
python main.py --task "Tesis de inversión Solana Q2 2026" --type research
python main.py --task "Analiza este backtest" --type office --file data.xlsx
python main.py --task "Plan de marketing para SaaS B2B" --type marketing
python main.py --task "Audita seguridad de esta API" --type security_audit

# Modo interactivo y UI
python main.py --interactive
python main.py --ui  # http://127.0.0.1:8000
```

## Pipelines disponibles (v2.0.0)

| Pipeline | Flag | Agentes | Tipo |
|----------|------|---------|------|
| DEV | `--type dev` | 6 agentes | Sub-pipeline |
| RESEARCH | `--type research` | 4 agentes (2 paralelo + 2 secuencial) | Sub-pipeline |
| CONTENT | `--type content` | 5 agentes | Sub-pipeline |
| OFFICE | `--type office` | 3 agentes | Sub-pipeline |
| QA | `--type qa` | 5 agentes | Sub-pipeline |
| TRADING | `--type trading` | 4 agentes | Sub-pipeline |
| PM | `--type pm` | 4 agentes | Sub-pipeline |
| ANALYTICS | `--type analytics` | 3 agentes | Sub-pipeline |
| MARKETING | `--type marketing` | 4 agentes | Sub-pipeline |
| PRODUCT | `--type product` | 4 agentes | Sub-pipeline |
| SECURITY_AUDIT | `--type security_audit` | 3 agentes | Sub-pipeline |
| DESIGN | `--type design` | 5 agentes | Sub-pipeline |
