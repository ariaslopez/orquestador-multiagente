# ROADMAP — CLAW Agent System

## Estado actual: v1.0.0 — Sistema estable con 7 pipelines operativos

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

## 🚧 Fase 8: Expandir pipelines macro a sub-pipelines reales

> Objetivo: CONTENT, QA, PM, OFFICE y TRADING pasan de 1 agente macro a cadenas de agentes especializados.
> Referencia: `ARCHITECTURE.md` — sección "Expansión de pipelines macro".

- [ ] **CONTENT pipeline** (5 sub-agentes)
  - [ ] `agents/content/topic_agent.py` — selecciona tema según contexto de mercado
  - [ ] `agents/content/writer_agent.py` — redacta contenido (hilo, post, newsletter)
  - [ ] `agents/content/editor_agent.py` — edita tono, longitud, hashtags
  - [ ] `agents/content/brand_agent.py` — verifica coherencia de marca
  - [ ] `agents/content/scheduler_agent.py` — propone calendario editorial

- [ ] **QA pipeline** (5 sub-agentes)
  - [ ] `agents/qa/static_analyzer.py` — análisis estático (linting, types)
  - [ ] `agents/qa/bug_hunter.py` — detección de bugs lógicos
  - [ ] `agents/qa/security_reviewer.py` — revisión de seguridad (OWASP)
  - [ ] `agents/qa/performance_profiler.py` — detección de cuellos de botella
  - [ ] `agents/qa/test_generator.py` — genera tests unitarios faltantes

- [ ] **PM pipeline** (4 sub-agentes)
  - [ ] `agents/pm/requirements_parser.py` — extrae requisitos de descripción libre
  - [ ] `agents/pm/backlog_builder.py` — crea backlog con épicas e historias
  - [ ] `agents/pm/sprint_planner.py` — prioriza con RICE/MoSCoW
  - [ ] `agents/pm/roadmap_generator.py` — genera roadmap con fases y milestones

- [ ] **OFFICE pipeline** (3 sub-agentes)
  - [ ] `agents/office/file_reader.py` — lectura y extracción de datos
  - [ ] `agents/office/data_analyzer.py` — análisis estadístico básico
  - [ ] `agents/office/report_writer.py` — genera reporte estructurado

- [ ] **TRADING pipeline** (4 sub-agentes)
  - [ ] `agents/trading/backtest_reader.py` — parsea resultados de backtest
  - [ ] `agents/trading/metrics_calculator.py` — Sharpe, drawdown, win rate
  - [ ] `agents/trading/risk_analyzer.py` — análisis de riesgo y exposición
  - [ ] `agents/trading/strategy_advisor.py` — recomendaciones de mejora

- [ ] Actualizar `config.yaml` con los 5 pipelines expandidos
- [ ] Actualizar `core/maestro.py` con los 5 builders nuevos
- [ ] Actualizar `examples/` con ejemplos de los pipelines expandidos

---

## 🔵 Fase 9: 5 pipelines nuevos (DESIGN, MARKETING, ANALYTICS, PRODUCT, SECURITY)

> Referencia: `ARCHITECTURE.md` — sección "Pipelines nuevos".

- [ ] **DESIGN pipeline** (5 agentes)
  - [ ] `agents/design/ui_agent.py` — genera especificaciones de UI/componentes
  - [ ] `agents/design/ux_agent.py` — arquitectura CSS y design tokens
  - [ ] `agents/design/brand_agent.py` — guías de marca y naming
  - [ ] `agents/design/a11y_agent.py` — auditoría WCAG 2.1
  - [ ] `agents/design/prompt_engineer.py` — prompts para generación de imágenes

- [ ] **MARKETING pipeline** (4 agentes)
  - [ ] `agents/marketing/strategy_agent.py` — estrategia de contenido y canales
  - [ ] `agents/marketing/copy_agent.py` — copywriting para landing, ads, emails
  - [ ] `agents/marketing/growth_agent.py` — loops de adquisición y pricing
  - [ ] `agents/marketing/analytics_agent.py` — métricas de marketing (CAC, LTV)

- [ ] **ANALYTICS pipeline** (3 agentes)
  - [ ] `agents/analytics/data_collector.py` — consolida datos de múltiples fuentes
  - [ ] `agents/analytics/insight_generator.py` — extrae insights de negocio
  - [ ] `agents/analytics/report_distributor.py` — formatea y distribuye reportes

- [ ] **PRODUCT pipeline** (4 agentes)
  - [ ] `agents/product/market_researcher.py` — análisis competitivo
  - [ ] `agents/product/feedback_synthesizer.py` — síntesis de feedback de usuarios
  - [ ] `agents/product/feature_prioritizer.py` — priorización data-driven
  - [ ] `agents/product/nudge_designer.py` — diseño de nudges de comportamiento

- [ ] **SECURITY_AUDIT pipeline** (3 agentes)
  - [ ] `agents/security/threat_modeler.py` — modelado de amenazas
  - [ ] `agents/security/code_reviewer.py` — revisión de código (OWASP Top 10)
  - [ ] `agents/security/compliance_checker.py` — GDPR/CCPA/API TOS compliance

- [ ] Clasificador en Maestro para 12 pipelines totales
- [ ] `config.yaml` con los 5 pipelines nuevos

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

# Modo interactivo y UI
python main.py --interactive
python main.py --ui  # http://127.0.0.1:8000
```

## Pipelines disponibles (v1.0.0)

| Pipeline | Flag | Agentes activos | Tipo |
|----------|------|-----------------|------|
| DEV | `--type dev` | 6 agentes reales | Sub-pipeline |
| RESEARCH | `--type research` | 4 agentes (2 paralelo + 2 secuencial) | Sub-pipeline |
| CONTENT | `--type content` | 1 agente macro | Pendiente expandir (Fase 8) |
| OFFICE | `--type office` | 1 agente macro | Pendiente expandir (Fase 8) |
| QA | `--type qa` | 1 agente macro | Pendiente expandir (Fase 8) |
| TRADING | `--type trading` | 1 agente macro | Pendiente expandir (Fase 8) |
| PM | `--type pm` | 1 agente macro | Pendiente expandir (Fase 8) |
