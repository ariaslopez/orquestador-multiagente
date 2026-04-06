# ROADMAP — CLAW Agent System v1.0.0

## Estado actual: v1.0.0 — Sistema estable con 7 pipelines

---

## ✅ Fase 1: DEV Pipeline Agents
- [x] `agents/dev/planner_agent.py` — genera plan de archivos y stack
- [x] `agents/dev/coder_agent.py` — genera codigo archivo por archivo
- [x] `agents/dev/reviewer_agent.py` — detecta y corrige bugs
- [x] `agents/dev/security_agent.py` — valida vulnerabilidades criticas
- [x] `agents/dev/executor_agent.py` — escribe en disco e instala deps
- [x] `agents/dev/git_agent.py` — hook Git/GitHub (stub seguro, sin PRs aun)

## ✅ Fase 2: Research, Content y Office Agents
- [x] `agents/research/webscout_agent.py` — busqueda web via DuckDuckGo
- [x] `agents/research/data_agent.py` — datos de mercado via CryptoDataTool
- [x] `agents/research/analyst_agent.py` — analisis de datos recopilados
- [x] `agents/research/thesis_agent.py` — genera tesis de inversion estructurada
- [x] `agents/content_agent.py` — contenido cripto con personalidades LLM
- [x] `agents/office_agent.py` — lee Excel, PDF, Word, CSV y genera reportes

## ✅ Fase 3: QA, Trading Analytics y PM Agents
- [x] `agents/qa_agent.py` — auditoria de codigo: bugs, seguridad, performance
- [x] `agents/trading_agent.py` — analisis de bots, backtests, metricas quant
- [x] `agents/pm_agent.py` — backlog, roadmap y sprints desde descripcion

## ✅ Fase 4: Infrastructure — Memoria y Seguridad
- [x] `infrastructure/memory_manager.py` — SQLite local + Supabase cloud
- [x] `infrastructure/security_layer.py` — 5 capas de proteccion
- [x] `infrastructure/security_sandbox.py` — sandbox de filesystem y comandos
- [x] `infrastructure/audit_logger.py` — registro completo de operaciones
- [x] `infrastructure/state_manager.py` — orquestador de estado de sesion
- [x] `infrastructure/output_manager.py` — manejo de carpetas de salida

## ✅ Fase 5: Tools
- [x] `tools/web_search.py` — busqueda DuckDuckGo sin API key
- [x] `tools/safe_filesystem.py` — filesystem auditado y seguro
- [x] `tools/file_ops.py` — operaciones de archivos de alto nivel
- [x] `tools/office_reader.py` — lectura de Excel, Word, PDF, PowerPoint
- [x] `tools/code_executor.py` — ejecucion segura (shell=False + shlex.split)
- [x] `tools/crypto_data.py` — datos de mercado crypto (CoinGecko/DeFiLlama)
- [x] `tools/git_ops.py` — integracion GitHub API (clone, read, list, PR)

## ✅ Fase 6: UI Dashboard
- [x] `ui/server.py` — FastAPI + WebSockets + API REST
- [x] `ui/index.html` — dashboard HTML con selector de pipeline
- [x] Endpoints REST: `/api/task`, `/api/sessions`, `/api/stats`
- [x] WebSocket live: `/ws/task`

## ✅ Fase 7: Documentacion y Ejemplos
- [x] `ROADMAP.md` — este archivo
- [x] `.gitignore` actualizado
- [x] `examples/dev_example.py` — ejemplo Dev pipeline
- [x] `examples/research_example.py` — ejemplo Research pipeline
- [x] `examples/content_example.py` — ejemplo Content pipeline
- [x] `examples/office_example.py` — ejemplo Office pipeline
- [x] `examples/qa_example.py` — ejemplo QA pipeline
- [x] `examples/trading_example.py` — ejemplo Trading pipeline
- [x] `examples/pm_example.py` — ejemplo PM pipeline

---

## Pendiente (deuda tecnica registrada)

### Seguridad
- [ ] Docker container efimero por tarea en `code_executor.py` (sandboxing real a nivel OS)
- [ ] Reemplazar `allowed_commands` strings por paths absolutos al interprete del venv
- [ ] Implementar o eliminar `scan_for_secrets: true` en config.yaml (ya implementado en sandbox, pendiente conectar con executor output)

### Performance
- [ ] Soporte paralelo real con `asyncio.gather` entre agentes en produccion (RESEARCH pipeline)

### Integraciones
- [ ] Plugin de Hyperspace como backend LLM local alternativo
- [ ] Docker-compose para deploy en servidor
- [ ] Fly.io deploy config
- [ ] Integracion avanzada con crypto-intelligence-hub (eventos y bots en vivo)
- [ ] Agente GitHubPR para abrir PRs automaticamente (extiende GitAgent + GitOpsTool)

### Documentacion
- [ ] Documentar modo offline (Ollama + ChromaDB) vs modo cloud (Groq + Supabase) en README
- [ ] CONTRIBUTING.md con convenciones del proyecto

---

## Uso rapido

```bash
# Setup inicial
cp .env.example .env
# Edita .env con tus API keys
python setup.py

# Verificar sistema
python main.py --doctor

# Ejecutar tarea
python main.py --task "Crea una API REST para senales de trading" --type dev
python main.py --task "Tesis de inversion para Solana Q2 2026" --type research
python main.py --task "Analiza este Excel de backtesting" --type office --file data.xlsx

# Modo interactivo
python main.py --interactive

# Dashboard web
python main.py --ui
```

## Pipelines disponibles

| Pipeline | Flag | Descripcion |
|----------|------|--------------|
| DEV | `--type dev` | Genera proyectos de software completos |
| RESEARCH | `--type research` | Tesis de inversion con datos web + mercado |
| CONTENT | `--type content` | Contenido cripto con personalidades |
| OFFICE | `--type office` | Analiza Excel, PDF, Word, CSV |
| QA | `--type qa` | Auditoria de codigo |
| TRADING | `--type trading` | Analytics de bots y backtests |
| PM | `--type pm` | Backlog y sprints desde descripcion |
