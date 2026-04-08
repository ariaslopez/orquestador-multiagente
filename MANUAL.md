# MANUAL TÉCNICO — CLAW Agent System

> Guía completa para desarrollar, depurar y extender el sistema.
> Versión: 2.2.2 · Última actualización: Abril 8, 2026

---

## Estado actual del sistema

### Lo que funciona hoy

| Componente | Archivo | Estado |
|---|---|---|
| Orquestación (Maestro) | `core/maestro.py` | ✅ 12 pipelines, clasificación LLM + keywords |
| Router de pipelines | `core/pipeline_router.py` | ✅ Sequential + parallel_then_sequential |
| Control de reintentos | `core/loop_controller.py` | ✅ Retry + recovery con límites |
| Router de LLMs | `core/api_router.py` | ✅ Ollama → Groq → Gemini → Hyperspace |
| Contexto compartido | `core/context.py` | ✅ AgentContext tipado + ctx.mcp_call() |
| Base de agente | `core/base_agent.py` | ✅ Tracing + memoria episódica automática |
| Memoria SQLite+Supabase | `infrastructure/memory_manager.py` | ✅ Persistencia dual |
| MCPHub (13 MCPs) | `infrastructure/mcp_hub.py` | ✅ Conectado a AgentContext (v2.2.2) |
| Audit logger | `infrastructure/audit_logger.py` | ✅ Tracing por agente |
| Input sanitizer | `infrastructure/input_sanitizer.py` | ✅ 13 patrones, 3 capas |
| Security sandbox | `infrastructure/security_sandbox.py` | ✅ Filesystem + comandos |
| Todos los agentes | `agents/*/` | ⚠️ Estructura real, calidad variable |
| Dashboard UI | `ui/server.py` + `ui/index.html` | ❓ Verificar estado |
| Tests E2E | `tests/test_e2e_pipelines.py` | ✅ 12 tests con mock LLM |
| Smoke tests + CI | `tests/smoke/` + `.github/workflows/ci.yml` | ⚠️ 1/5 smoke tests activos (Fase 14) |

### Lo que aún falta completar

1. **Smoke tests completos** — existe `tests/smoke/test_mcp_context.py` + CI activo; faltan 4 tests adicionales (Fase 14).
2. **Rate limiting en MCPs** — Brave Search y CoinGecko tienen límites de free tier sin throttle todavía.
3. **CoderAgent real** — pendiente conectar `context7` + `github_mcp` (Fase 13).
4. **ReportDistributorAgent real** — pendiente conectar `slack` MCP (Fase 13).
5. **Dashboard UI verificado** — `ui/server.py` + `ui/index.html` existen pero no han sido auditados en v2.2.x.

---

## Setup de desarrollo

```bash
# Clonar y entrar
git clone https://github.com/ariaslopez/orquestador-multiagente
cd orquestador-multiagente

# Entorno virtual
python -m venv venv
source venv/bin/activate          # Linux/Mac
venv\Scripts\activate              # Windows

# Dependencias
pip install -r requirements.txt

# Configurar .env
cp .env.example .env
# Editar .env — mínimo: GROQ_API_KEY

# Ollama (recomendado para desarrollo local)
winget install Ollama.Ollama       # Windows
brew install ollama                # Mac
ollama pull qwen2.5-coder:7b-q4_K_M

# Verificar todo
python main.py --doctor
```

### Variables de entorno por prioridad

```env
# ── OBLIGATORIAS ──────────────────────────────────
GROQ_API_KEY=tu_clave              # https://console.groq.com (gratis)

# ── RECOMENDADAS ────────────────────────────────
OLLAMA_ENABLED=true
OLLAMA_HW_PROFILE=cpu_24gb        # ver perfiles abajo
GEMINI_API_KEY=tu_clave           # fallback LLM
GITHUB_TOKEN=ghp_...              # para github_mcp

# ── SUPABASE (memoria cloud) ────────────────────────
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=tu_anon_key

# ── MCPs opcionales ───────────────────────────────
BRAVE_API_KEY=your_key            # para brave_search
CONTEXT7_API_KEY=your_key         # para context7
DEEPWIKI_API_KEY=your_key         # para deepwiki
OKX_API_KEY=your_key              # para okx
SLACK_BOT_TOKEN=xoxb-...          # para slack
N8N_WEBHOOK_URL=https://...       # para n8n
COINGECKO_API_KEY=your_key        # opcional, free tier sin key
MCP_TIMEOUT=30                    # timeout en segundos

# ── SEGURIDAD ───────────────────────────────────
GITHUB_CONFIRM_BEFORE_PUSH=true
```

### Perfiles de hardware Ollama

| Perfil | Hardware | GPU layers | Context |
|---|---|---|---|
| `cpu_24gb` | CPU + 24 GB RAM (default) | 4 (iGPU) | 32,768 |
| `gpu_8gb` | RTX 3070 / RX 6700 XT | 33 | 32,768 |
| `gpu_16gb` | RTX 4070 / RX 7900 | 43 | 65,536 |
| `gpu_24gb` | RTX 4090 / RX 7900 XTX | 65 | 128,000 |

---

## Estructura de directorios — decisiones de diseño

```
core/          → orquestación pura, sin I/O externo
agents/        → un directorio por pipeline, un archivo por agente
infrastructure/→ servicios de soporte (memoria, seguridad, MCPs)
tools/         → funciones utilitarias sin estado propio
ui/            → servidor FastAPI + frontend
tests/         → tests que no requieren API keys (mock LLM)
examples/      → scripts ejecutables por pipeline
```

### ¿Por qué hay archivos sueltos en `agents/`?

`agents/trading_agent.py`, `agents/qa_agent.py`, etc. son **tombstones de compatibilidad** desde v2.2.2.
Redirigen a los sub-agentes reales en `agents/trading/`, `agents/qa/`, etc.
No usarlos en código nuevo. Se eliminarán en v3.

### ¿Por qué existen `orchestrator.py` y `pipeline.py` en `core/`?

Son aliases de compatibilidad desde v2.2.2. `Maestro` + `PipelineRouter` + `LoopController`
son los entrypoints reales. Los aliases se eliminarán en v3.

---

## Cómo crear un agente nuevo

```python
# agents/<pipeline>/<nombre>_agent.py
from core.base_agent import BaseAgent
from core.context import AgentContext

class NombreAgent(BaseAgent):
    """
    Descripción de qué hace este agente y en qué pipeline vive.
    MCPs que usa: brave_search, mcp_memory
    """

    async def run(self, context: AgentContext) -> AgentContext:
        # Memoria previa disponible automáticamente (BaseAgent._before_run)
        task = context.task
        prev_output = context.get("prev_agent_output")

        # Llamar MCP — funciona desde v2.2.2
        if context.is_mcp_available("brave_search"):
            results = await context.mcp_call(
                "brave_search", "search", {"query": task}
            )

        prompt = f"""
        Tarea: {task}
        Contexto previo: {prev_output}
        ...
        """

        response = await self.llm(prompt, context)
        context.set("nombre_output", response)
        # Memoria guardada automáticamente (BaseAgent._after_run)
        return context
```

---

## Cómo llamar un MCP

```python
# Verificar disponibilidad
if context.is_mcp_available("brave_search"):
    results = await context.mcp_call(
        "brave_search",
        "search",
        {"query": "Bitcoin 2026", "count": 10}
    )

# Ver todos los MCPs disponibles
print(context.mcp.available())

# Ver MCPs de una categoría
print(context.mcp.available("trading"))

# Ver estado completo
print(context.mcp.status())
```

### MCPs que funcionan sin ninguna configuración

```python
# mcp_memory — guardar y recuperar memoria (automático vía BaseAgent)
await context.mcp_call("mcp_memory", "save", {"key": "...", "value": "..."})
await context.mcp_call("mcp_memory", "retrieve", {"key": "..."})

# sequential_thinking — razonamiento estructurado
await context.mcp_call("sequential_thinking", "decompose", {"problem": task, "steps": 5})

# coingecko — datos de criptomonedas
await context.mcp_call("coingecko", "get_price", {"ids": "bitcoin", "vs_currencies": "usd"})

# semgrep — análisis de seguridad
await context.mcp_call("semgrep", "scan", {"code": source_code, "language": "python"})

# playwright — automatización web
await context.mcp_call("playwright", "navigate", {"url": "https://..."})
```

---

## Cómo ejecutar tests

```bash
# Todos (no requieren API keys)
pytest tests/ -v

# Por módulo
pytest tests/test_pipeline_imports.py -v     # 52 agentes + 12 pipelines
pytest tests/test_e2e_pipelines.py -v        # 12 tests E2E con mock LLM
pytest tests/test_input_sanitizer.py -v      # Seguridad de inputs
pytest tests/smoke/test_mcp_context.py -v    # MCPHub + AgentContext (CI activo)

# Con cobertura
pytest tests/ --cov=core --cov=agents --cov-report=term-missing
```

### Smoke tests pendientes (Fase 14)

```bash
# Faltan 4 de 5 smoke tests — crearlos es prioridad en Fase 14
pytest tests/smoke/test_pipeline_classification.py
pytest tests/smoke/test_loop_controller_retry.py
pytest tests/smoke/test_mcp_hub_fallback.py
pytest tests/smoke/test_supabase_persistence.py
pytest tests/smoke/test_api_router_fallback.py
```

---

## Debugging común

### El sistema usa el provider equivocado
```bash
python main.py --doctor
# Muestra estado de todos los providers y cuál está activo
```

### Un agente no encuentra otro agente
```python
# Verificar que el import en maestro.py apunta al directorio correcto
# ✅ from agents.trading.backtest_reader import BacktestReaderAgent
# ❌ from agents.trading_agent import TradingAgent  ← tombstone, no usarlo en código nuevo
```

### Un MCP no responde
```python
from infrastructure.mcp_hub import get_mcp_hub
hub = get_mcp_hub()
print(hub.status())          # muestra todos los MCPs y si están configurados
print(hub.available())       # solo los que tienen config válida
```

### Ver logs de un pipeline en tiempo real
```bash
tail -f data/claw.log
# O filtrar por pipeline
tail -f data/claw.log | grep "\[trading\]"
```

### Verificar que la memoria persiste
```python
from infrastructure.memory_manager import MemoryManager
mm = MemoryManager()
recent = mm.get_recent_sessions(limit=5)
print(recent)
```

---

## CLI — referencia completa

```bash
# Ejecución por pipeline
python main.py --task "<tarea>" --type <pipeline>
python main.py --task "<tarea>" --type dev --file src/module.py

# Clasificación automática
python main.py --task "¿Cuál es el Sharpe de este bot?"

# Sistema
python main.py --doctor          # Diagnóstico completo: LLMs + MCPs + memoria
python main.py --interactive     # Loop de tareas en terminal
python main.py --ui              # Dashboard → http://127.0.0.1:8000
python main.py --history         # Últimas 20 sesiones
python main.py --usage           # Tokens y costos acumulados
```

### Pipelines disponibles

```
dev · research · content · office · qa · pm
trading · analytics · marketing · product · security_audit · design
```

---

## Contribuir

1. Fork + branch descriptivo: `feat/mcp-context-connection` o `fix/planner-sequential-thinking`
2. Un PR por feature o fix
3. Los tests deben pasar: `pytest tests/ -v`
4. Actualizar `ROADMAP.md` marcando ítems completados
5. Si creas un agente nuevo, seguir la estructura de `NombreAgent` documentada arriba
6. Si conectas un MCP nuevo, agregarlo a la tabla de `README.md`

---

## Changelog

### v2.2.2 (Abril 2026)
- `core/context.py` — `AgentContext.inject_mcp()` + helpers `is_mcp_available()` / `mcp_call()`
- `core/base_agent.py` — hooks `_before_run()` / `_after_run()` para memoria episódica automática
- `agents/dev/planner_agent.py` v2 — usa `sequential_thinking` MCP para descomposición de tareas
- `agents/research/` v2 — WebScoutAgent (brave_search + fallback), AnalystAgent, ThesisAgent
- `agents/trading/data_agent.py` v2 — coingecko + okx + supabase_mcp como pipeline TRADING etapa 0
- Stubs en `agents/` raíz convertidos en tombstones de compatibilidad (PR-2)
- `core/orchestrator.py` y `core/pipeline.py` — aliases de compatibilidad hacia Maestro / PipelineRouter
- Logging centralizado en `data/claw.log` + AuditLogger sincronizado con Supabase
- `tests/smoke/test_mcp_context.py` + `.github/workflows/ci.yml` — CI activo en cada push

### v2.1.0 (Abril 2026)
- `infrastructure/mcp_hub.py` — proxy universal para 13 MCPs
- `core/api_router.py` — estrategia local_first con 4 providers y perfiles de hardware
- Bugs corregidos: double retry silencioso, race condition singleton,
  costo contra provider equivocado, @retry sobre async def
- Documentación completa actualizada (README, ROADMAP, ARCHITECTURE, MANUAL)

### v2.0.0 (Marzo 2026)
- 12 pipelines operativos, 70 agentes
- Input sanitizer (13 patrones, 3 capas)
- Tracing automático en BaseAgent
- 12 tests E2E con mock LLM
- Dashboard métricas en GET /api/metrics

### v1.0.0 (Febrero 2026)
- DEV pipeline completo (6 agentes reales)
- RESEARCH pipeline (4 agentes, parallel_then_sequential)
- Infrastructure base (memory, security, audit)
