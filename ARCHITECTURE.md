# ARCHITECTURE — CLAW Agent System

> Mapa completo del sistema: 70 agentes del Agency Registry → 12 pipelines de CLAW.
> Este documento es la fuente de verdad para el diseño de agentes y pipelines.

**Versión:** 2.1.0 · **Última actualización:** Abril 7, 2026

---

## Principio de diseño

Los 70 agentes del Registry son **roles especializados**, no pipelines independientes. Cada pipeline de CLAW es un flujo de trabajo donde N agentes colaboran en secuencia o en paralelo, compartiendo un `AgentContext` tipado. El `MCPHub` expone 13 herramientas externas que cualquier agente puede invocar a través del contexto.

```
AGENT_REGISTRY (70 roles)
         │
         ▼
  12 pipelines CLAW
         │
    ┌────┴────┐
    │ Maestro │  ← clasifica tarea → pipeline correcto
    └────┬────┘
         │
    ┌────┴──────────┐
    │  AgentContext  │ ← estado compartido + MCPHub (13 tools)
    └───────────────┘
```

---

## Estado real de implementación

| Pipeline | Agentes | Estado real | Notas |
|---|---|---|---|
| DEV | 6 en directorio | ✅ Sub-agentes reales | PlannerAgent sin sequential_thinking aún |
| RESEARCH | 4 en directorio | ✅ Sub-agentes reales | WebScout usa DuckDuckGo, pendiente brave_search |
| CONTENT | 5 en directorio | ✅ Estructura creada | Verificar implementación de cada agente |
| QA | 5 en directorio | ✅ Estructura creada | Verificar implementación de cada agente |
| PM | 4 en directorio | ✅ Estructura creada | Verificar implementación de cada agente |
| OFFICE | 3 en directorio | ✅ Estructura creada | Verificar implementación de cada agente |
| TRADING | 4 en directorio | ✅ Estructura creada | DataAgent pendiente coingecko + okx |
| ANALYTICS | 3 en directorio | ✅ Estructura creada | ReportDistributor pendiente slack |
| MARKETING | 4 en directorio | ✅ Estructura creada | Verificar implementación |
| PRODUCT | 4 en directorio | ✅ Estructura creada | Verificar implementación |
| SECURITY_AUDIT | 3 en directorio | ✅ Estructura creada | Verificar implementación |
| DESIGN | 5 en directorio | ✅ Estructura creada | Verificar implementación |

> **Nota:** "Estructura creada" significa que los archivos existen y heredan de BaseAgent.
> La calidad real de cada `run()` debe verificarse pipeline por pipeline.

> **Stubs redundantes en raíz:** Existen `agents/trading_agent.py`, `agents/qa_agent.py`,
> `agents/content_agent.py`, `agents/pm_agent.py`, `agents/office_agent.py` como archivos
> sueltos (~800-900 bytes cada uno). Son de una versión anterior y deben eliminarse.
> Ver `ROADMAP.md → Fase 12 - Paso 2`.

---

## DEV pipeline

**Trigger keywords:** `crea`, `genera`, `construye`, `proyecto`, `api`, `app`, `código`, `refactor`

```
PlannerAgent → CoderAgent → ReviewerAgent → SecurityAgent → ExecutorAgent → GitAgent
    │               │             │               │               │             │
  plan +          genera        revisa y        valida          ejecuta       commit
sequential_      código        corrige         seguridad        en disco      + PR
thinking¹        con ctx7²
```

¹ `sequential_thinking` pendiente de conectar (Fase 12 - Paso 5)
² `context7` pendiente de conectar (Fase 13)

**MCPs objetivo por agente:**
- `PlannerAgent` → `sequential_thinking` + `mcp_memory`
- `CoderAgent` → `context7` + `github_mcp`
- `SecurityAgent` → `semgrep`
- `GitAgent` → `github_mcp`

**Agentes del Registry mapeados:**
- `engineering-backend-architect` → PlannerAgent
- `engineering-senior-developer` → CoderAgent + ReviewerAgent
- `engineering-security-engineer` → SecurityAgent
- `engineering-devops-automator` → ExecutorAgent + GitAgent

---

## RESEARCH pipeline

**Trigger keywords:** `tesis`, `análisis`, `inversión`, `investigación`, `mercado`, `precio`, `token`

```
         ┌─ WebScoutAgent ──┐
         │  brave_search¹   │
         │                  ▼
         │           AgentContext
         │                  │
         └─ DataAgent ──────┘
           coingecko + okx²  │
                             ▼
                       AnalystAgent
                             │
                             ▼
                       ThesisAgent
```

¹ Actualmente usa DuckDuckGo; pendiente upgrade a `brave_search`
² `coingecko` funciona sin API key; `okx` requiere `OKX_API_KEY`

**Ejecución:** `parallel_then_sequential`

---

## TRADING pipeline

**Trigger keywords:** `backtest`, `sharpe`, `drawdown`, `bot`, `estrategia`, `señales`

```
BacktestReader → MetricsCalculator → RiskAnalyzer → StrategyAdvisor
   parsea          Sharpe, DD,         exposición,    recomendaciones
   resultados      win rate            concentración
```

**MCPs objetivo:**
- `DataAgent` / `BacktestReader` → `coingecko` + `okx` + `supabase_mcp`

---

## ANALYTICS pipeline

**Trigger keywords:** `reporte`, `KPIs`, `métricas`, `dashboard`, `consolida`

```
DataCollector → InsightGenerator → ReportDistributor
 consolida        insights de        formatea y
 fuentes          negocio            distribuye vía Slack¹
```

¹ `ReportDistributorAgent` pendiente conectar `slack` MCP

---

## CONTENT pipeline

**Trigger keywords:** `contenido`, `tweet`, `hilo`, `post`, `newsletter`, `redacta`

```
TopicAgent → WriterAgent → EditorAgent → BrandAgent → SchedulerAgent
```

---

## QA pipeline

**Trigger keywords:** `audita`, `revisa`, `bugs`, `tests`, `calidad`, `vulnerabilidades`

```
StaticAnalyzer → BugHunter → SecurityReviewer → PerformanceProfiler → TestGenerator
```

**MCPs objetivo:**
- `SecurityReviewer` → `semgrep` + `deepwiki`
- `TestGenerator` → `playwright`

---

## PM pipeline

**Trigger keywords:** `roadmap`, `backlog`, `sprint`, `épicas`, `historias`, `planifica`

```
RequirementsParser → BacklogBuilder → SprintPlanner → RoadmapGenerator
```

---

## OFFICE pipeline

**Trigger keywords:** `excel`, `csv`, `pdf`, `word`, `archivo`, `analiza`

```
FileReader → DataAnalyzer → ReportWriter
```

---

## MARKETING pipeline

**Trigger keywords:** `marketing`, `campaña`, `copy`, `landing`, `crecimiento`, `adquisición`

```
StrategyAgent → CopyAgent → GrowthAgent → AnalyticsAgent
```

---

## PRODUCT pipeline

**Trigger keywords:** `competidores`, `validar idea`, `feedback`, `feature`, `prioriza`

```
MarketResearcher → FeedbackSynthesizer → FeaturePrioritizer → NudgeDesigner
```

---

## SECURITY_AUDIT pipeline

**Trigger keywords:** `threat model`, `compliance`, `GDPR`, `vulnerabilidades críticas`

```
ThreatModeler → CodeReviewer → ComplianceChecker
```

**MCPs objetivo:**
- `ThreatModeler` → `semgrep`
- `CodeReviewer` → `deepwiki` + `semgrep`

---

## DESIGN pipeline

**Trigger keywords:** `diseña`, `UI`, `componente`, `marca`, `paleta`, `wireframe`

```
UIAgent → UXAgent → BrandAgent → A11yAgent → PromptEngineer
```

---

## MCPHub — Mapa de MCPs por agente

```
MCP                  → Agentes que lo usan
─────────────────────────────────────────────
mcp_memory           → TODOS (BaseAgent lo inyecta)
sequential_thinking  → PlannerAgent, Maestro
brave_search         → WebScoutAgent
context7             → CoderAgent
deepwiki             → CoderAgent, SecurityReviewer
supabase_mcp         → DataAgent, ReportDistributor, DataCollector
coingecko            → DataAgent, BacktestReader
okx                  → DataAgent, BacktestReader
github_mcp           → CoderAgent, GitAgent
semgrep              → SecurityAgent, ThreatModeler, CodeReviewer
playwright           → TestGenerator
slack                → ReportDistributor
n8n                  → Cualquier agente de automatización
```

---

## Convenciones de implementación

### Estructura de un agente

```python
# agents/<pipeline>/<nombre>_agent.py
from core.base_agent import BaseAgent
from core.context import AgentContext

class NombreAgent(BaseAgent):
    async def run(self, context: AgentContext) -> AgentContext:
        # 1. Recuperar memoria previa (automático vía BaseAgent cuando esté conectado)
        # 2. Leer inputs del contexto
        # 3. Opcionalmente llamar MCPs: await context.mcp.call("mcp_name", "tool", {...})
        # 4. Construir prompt
        # 5. Llamar self.llm(prompt, context)
        # 6. Parsear respuesta
        # 7. Escribir outputs al contexto
        # 8. Retornar contexto
        return context
```

### Llamar un MCP desde un agente

```python
# Ejemplo: WebScoutAgent usando brave_search
result = await context.mcp.call(
    "brave_search",
    "search",
    {"query": "Bitcoin price analysis 2026", "count": 10}
)

# Ejemplo: PlannerAgent usando sequential_thinking
plan = await context.mcp.call(
    "sequential_thinking",
    "decompose",
    {"problem": context.task, "steps": 5}
)

# Verificar disponibilidad antes de llamar
if context.mcp.is_available("brave_search"):
    result = await context.mcp.call("brave_search", "search", {...})
else:
    # fallback a DuckDuckGo
    result = await tools.web_search(query)
```

### Registrar un pipeline nuevo

1. Crear agentes en `agents/<pipeline>/`
2. Añadir entrada en `config.yaml` bajo `pipelines:`
3. Añadir builder en `core/maestro.py` → método `_build_<pipeline>_pipeline()`
4. Añadir keywords en `core/maestro.py` → `_classify_task()`
5. Crear ejemplo en `examples/<pipeline>_example.py`
6. Actualizar `ROADMAP.md` con ítems completados

### Patrones de ejecución

```yaml
# config.yaml — pipeline secuencial
dev:
  type: sequential
  agents: [planner, coder, reviewer, security, executor, git]

# config.yaml — paralelo + secuencial
research:
  type: parallel_then_sequential
  parallel_agents: [web_scout, data]
  sequential_agents: [analyst, thesis]
```

---

## Cobertura del Registry

```
70 agentes del Registry
├── 12 pipelines CLAW               ← ~52 agentes activos
│   ├── 7 pipelines v1.0.0–v2.0.0
│   └── 5 pipelines Fase 9
├── ~12 agentes transversales       ← capacidades auxiliares
└── 6 agentes Spatial/XR            ← out of scope activo
```

**Cobertura funcional:** ~94% de los 70 agentes tienen lugar en la arquitectura.
