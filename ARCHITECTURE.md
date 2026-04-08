# ARCHITECTURE — CLAW Agent System

> Mapa completo del sistema: 70 agentes del Agency Registry → 12 pipelines de CLAW.
> Este documento es la fuente de verdad para el diseño de agentes, pipelines y skills.

**Versión:** 2.3.0 · **Última actualización:** Abril 8, 2026

---

## Principio de diseño

Los 70 agentes del Registry son **roles especializados**, no pipelines independientes. Cada pipeline de CLAW es un flujo de trabajo donde N agentes colaboran en secuencia o en paralelo, compartiendo un `AgentContext` tipado. El `MCPHub` expone 13 herramientas externas que cualquier agente puede invocar a través del contexto mediante `ctx.mcp_call()`. El sistema de **skills** (Fase 17-A) añade una capa declarativa de recetas reutilizables por pipeline, sin modificar el código Python existente.

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
    │  AgentContext  │ ← estado compartido + MCPHub (13 tools) + ctx.mcp_call()
    └───────────────┘
         │
    ┌───┴──────┐
    │ skills/*.md │ ← recetas declarativas por pipeline (Fase 17-A, pendiente)
    └──────────┘
```

---

## Estado real de implementación

| Pipeline | Agentes | Estado real | Notas |
|---|---|---|---|
| DEV | 6 en directorio | ✅ Sub-agentes reales | PlannerAgent usa sequential_thinking; CoderAgent usa context7 + github_mcp (v2.3.0) |
| RESEARCH | 4 en directorio | ✅ Sub-agentes reales (v2) | WebScoutAgent usa brave_search + fallback DuckDuckGo |
| CONTENT | 5 en directorio | ✅ Estructura creada | Verificar implementación de cada agente |
| QA | 5 en directorio | ✅ Estructura creada | Verificar implementación de cada agente |
| PM | 4 en directorio | ✅ Estructura creada | Verificar implementación de cada agente |
| OFFICE | 3 en directorio | ✅ Estructura creada | Verificar implementación de cada agente |
| TRADING | 4+1 en directorio | ✅ Estructura creada | DataAgent real con coingecko + okx + supabase_mcp (v2.3.0) |
| ANALYTICS | 3 en directorio | ✅ Estructura creada | ReportDistributorAgent real con supabase_mcp + slack (v2.3.0) |
| MARKETING | 4 en directorio | ✅ Estructura creada | Verificar implementación |
| PRODUCT | 4 en directorio | ✅ Estructura creada | Verificar implementación |
| SECURITY_AUDIT | 3 en directorio | ✅ Estructura creada | Verificar implementación |
| DESIGN | 5 en directorio | ✅ Estructura creada | Verificar implementación |

> **Nota:** "Estructura creada" significa que los archivos existen y heredan de BaseAgent.
> La calidad real de cada `run()` debe verificarse pipeline por pipeline.

> **Stubs en raíz convertidos a tombstones (v2.2.2):** `agents/trading_agent.py`,
> `agents/qa_agent.py`, `agents/content_agent.py`, `agents/pm_agent.py`,
> `agents/office_agent.py` son ahora aliases de compatibilidad que redirigen a los
> sub-agentes reales en `agents/trading/`, `agents/qa/`, etc.
> No usarlos en código nuevo. Se eliminarán en v3.

---

## Sub-agentes y colaboradores por pipeline crítico

> **Contexto:** Esta sección documenta la propuesta de sub-agentes colaboradores
> resultado de la auditoría de Abril 2026. Aplica dos patrones:
>
> - **Nuevo agente en el pipeline** — cuando el colaborador necesita memoria propia,
>   logs, métricas o reutilización independiente. Se modela como un paso más del pipeline.
> - **Lógica interna del agente** — cuando es un microdetalle de calidad interno al agente
>   (más MCPs, más prompts, validación local). Se mantiene dentro del `run()` existente.
>
> El criterio de decisión: ¿quieres medir, testear o reusar ese colaborador por separado?
> Si sí → agente nuevo. Si no → lógica interna.

### DEV — Sub-agentes colaboradores propuestos

```
PlannerAgent → [RefactorAnalyzer*] → CoderAgent → [TestValidatorAgent*] → ReviewerAgent → SecurityAgent → ExecutorAgent → [GitConfirmAgent*] → GitAgent

* = sub-agente colaborador propuesto
```

| Sub-agente propuesto | Patrón | Función | MCPs |
|---|---|---|---|
| `RefactorAnalyzer` | Nuevo agente (paso 2) | Analiza el codebase antes de codear: detecta módulos afectados, dependencias y riesgo de regresión | `context7` + `github_mcp` |
| `TestValidatorAgent` | Nuevo agente (paso 4) | Valida que el código generado tiene tests mínimos antes de pasar a Review | `playwright` (smoke) |
| `GitConfirmAgent` | Lógica interna de GitAgent | Solicita confirmación antes de push a main; crea rama feature/* automáticamente | `github_mcp` |

**Pipeline extendido (config.yaml):**
```yaml
dev:
  agents: [planner, refactor_analyzer, coder, test_validator, reviewer, security, executor, git]
  mode: sequential
```

**Criterio de done:** `RefactorAnalyzer` y `TestValidatorAgent` se implementan en Fase 17-B
junto con GitAgent real. `GitConfirmAgent` es lógica interna de `git_agent.py`.

---

### RESEARCH — Sub-agentes colaboradores propuestos

```
WebScoutAgent ──┐
                ├→ [SourceValidatorAgent*] → AnalystAgent → [BiasDetectorAgent*] → ThesisAgent
DataAgent ──────┘

* = sub-agente colaborador propuesto
```

| Sub-agente propuesto | Patrón | Función | MCPs |
|---|---|---|---|
| `SourceValidatorAgent` | Nuevo agente (paralelo → paso 3) | Valida calidad y credibilidad de fuentes recolectadas (deduplicación, scoring de dominio, fecha) | `mcp_memory` |
| `BiasDetectorAgent` | Lógica interna de AnalystAgent | Detecta sesgo en síntesis: fuentes unilaterales, falta de perspectivas contrarias | `sequential_thinking` |

**Pipeline extendido (config.yaml):**
```yaml
research:
  agents: [web_scout, data, source_validator, analyst, thesis]
  mode: parallel_then_sequential
  parallel_agents: [web_scout, data]
  sequential_agents: [source_validator, analyst, thesis]
```

**Prioridad:** Alta. `SourceValidatorAgent` mejora directamente la calidad de la tesis de inversión.
Implementar junto con rate limiting de MCPHub en Fase 14.

---

### QA — Sub-agentes colaboradores propuestos

```
StaticAnalyzer → BugHunter → [RegressionAgent*] → SecurityReviewer → PerformanceProfiler → [ReportFormatterAgent*] → TestGenerator

* = sub-agente colaborador propuesto
```

| Sub-agente propuesto | Patrón | Función | MCPs |
|---|---|---|---|
| `RegressionAgent` | Nuevo agente (paso 3) | Verifica que los bugs encontrados por BugHunter no rompen tests existentes | `playwright` |
| `ReportFormatterAgent` | Nuevo agente (paso 6) | Consolida todos los findings en un reporte estructurado con severidades OWASP | `supabase_mcp` |

**Pipeline extendido (config.yaml):**
```yaml
qa:
  agents: [static_analyzer, bug_hunter, regression_agent, security_reviewer, performance_profiler, report_formatter, test_generator]
  mode: sequential
```

**Prioridad:** Media. `ReportFormatterAgent` es el más impactante porque standariza el output
de QA y lo hace consumible por SECURITY_AUDIT y por el dashboard UI.

---

### TRADING — Sub-agentes colaboradores propuestos

```
BacktestReader → [DataEnricherAgent*] → MetricsCalculator → RiskAnalyzer → [ScenarioSimulatorAgent*] → StrategyAdvisor

* = sub-agente colaborador propuesto
```

| Sub-agente propuesto | Patrón | Función | MCPs |
|---|---|---|---|
| `DataEnricherAgent` | Nuevo agente (paso 2) | Enriquece backtests con datos on-chain, noticias y correlaciones de mercado | `coingecko` + `brave_search` |
| `ScenarioSimulatorAgent` | Lógica interna de RiskAnalyzer | Simula N escenarios de mercado (bull/bear/black swan) sobre la estrategia | `coingecko` |

**Prioridad:** Media. `DataEnricherAgent` se implementa en Fase 17-B.
`ScenarioSimulatorAgent` es lógica interna de `risk_analyzer.py`, implementar en la
revisión de calidad de Fase 14-post.

---

### ANALYTICS — Sub-agentes colaboradores propuestos

```
DataCollector → [DataValidatorAgent*] → InsightGenerator → [TrendComparatorAgent*] → ReportDistributor

* = sub-agente colaborador propuesto
```

| Sub-agente propuesto | Patrón | Función | MCPs |
|---|---|---|---|
| `DataValidatorAgent` | Nuevo agente (paso 2) | Valida integridad de datos: nulls, outliers, esquema; rechaza datos corruptos antes de análisis | `supabase_mcp` |
| `TrendComparatorAgent` | Lógica interna de InsightGenerator | Compara KPIs actuales vs período anterior y marca tendencias significativas | `supabase_mcp` |

**Prioridad:** Alta. `DataValidatorAgent` evita análisis con datos corruptos (fallo silencioso
más crítico de este pipeline). Implementar junto con contratos de datos en Fase 15.

---

### SECURITY_AUDIT — Sub-agentes colaboradores propuestos

```
ThreatModeler → [AttackSurfaceMapperAgent*] → CodeReviewer → ComplianceChecker → [RemediationAdvisorAgent*]

* = sub-agente colaborador propuesto
```

| Sub-agente propuesto | Patrón | Función | MCPs |
|---|---|---|---|
| `AttackSurfaceMapperAgent` | Nuevo agente (paso 2) | Mapea superficie de ataque: endpoints públicos, inputs, dependencias, secrets | `semgrep` + `github_mcp` |
| `RemediationAdvisorAgent` | Nuevo agente (paso 5) | Por cada finding, genera ticket con: descripción, severidad, fix sugerido y test de regresión | `supabase_mcp` + `mcp_memory` |

**Pipeline extendido (config.yaml):**
```yaml
security_audit:
  agents: [threat_modeler, attack_surface_mapper, code_reviewer, compliance_checker, remediation_advisor]
  mode: sequential
```

**Prioridad:** Alta. `RemediationAdvisorAgent` cierra el loop de seguridad convirtiendo findings
en acciones concretas con trazabilidad. Es el sub-agente de mayor ROI de este pipeline.

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

¹ `sequential_thinking` conectado en v2.2.2 vía `ctx.mcp_call("sequential_thinking", ...)`
² `context7` + `github_mcp` conectados en v2.3.0 (CoderAgent real)

**MCPs activos por agente:**
- `PlannerAgent` → `sequential_thinking` + `mcp_memory` ✅ v2.2.2
- `CoderAgent` → `context7` + `github_mcp` ✅ v2.3.0
- `SecurityAgent` → `semgrep`
- `GitAgent` → `github_mcp`

**Skills planificadas (Fase 17-A):**
- `implement_feature` — feature completa end-to-end (plan → código → review → PR)
- `code_review` — revisión con criterios definidos y output estructurado
- `write_tests` — suite de tests para un módulo dado
- `refactor_module` — refactor sin romper comportamiento observable

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
                       AnalystAgent (v2)
                             │
                             ▼
                       ThesisAgent (v2)
```

¹ Usa `brave_search` MCP con fallback automático a DuckDuckGo (v2.2.2)
² `coingecko` funciona sin API key; `okx` requiere `OKX_API_KEY`

**Ejecución:** `parallel_then_sequential`

**Skills planificadas (Fase 17-A):**
- `web_research` — investigación web multi-fuente con síntesis estructurada
- `competitor_analysis` — análisis de competidores con múltiples fuentes
- `summarize_sources` — resumir N fuentes en un documento estructurado

---

## TRADING pipeline

**Trigger keywords:** `backtest`, `sharpe`, `drawdown`, `bot`, `estrategia`, `señales`

```
BacktestReader → MetricsCalculator → RiskAnalyzer → StrategyAdvisor
   parsea          Sharpe, DD,         exposición,    recomendaciones
   resultados      win rate            concentración
```

**MCPs activos:**
- `DataAgent` / `BacktestReader` → `coingecko` + `okx` + `supabase_mcp` ✅ v2.2.2

**Nota sobre skills:** TRADING está excluido del v1 del skills system (Fase 17-A).
El pipeline funciona con sus agentes actuales. Se incorporará al sistema de skills
en v2 de la Fase 17-A, después de validar el esquema con los 11 pipelines restantes.

---

## ANALYTICS pipeline

**Trigger keywords:** `reporte`, `KPIs`, `métricas`, `dashboard`, `consolida`

```
DataCollector → InsightGenerator → ReportDistributor
 consolida        insights de        formatea y
 fuentes          negocio            distribuye vía Slack ✅ v2.3.0
```

**MCPs activos:**
- `ReportDistributor` → `supabase_mcp` + `slack` ✅ v2.3.0

**Skills planificadas (Fase 17-A):**
- `kpi_report` — reporte semanal/mensual de KPIs con tendencias
- `funnel_analysis` — análisis de embudo de conversión
- `cohort_analysis` — análisis de retención por cohortes

---

## CONTENT pipeline

**Trigger keywords:** `contenido`, `tweet`, `hilo`, `post`, `newsletter`, `redacta`

```
TopicAgent → WriterAgent → EditorAgent → BrandAgent → SchedulerAgent
```

**Skills planificadas (Fase 17-A):**
- `longform_to_social` — convertir contenido largo a posts por red social
- `newsletter_issue` — generar un número completo de newsletter
- `landing_copy` — copy de landing page con estructura AIDA

---

## QA pipeline

**Trigger keywords:** `audita`, `revisa`, `bugs`, `tests`, `calidad`, `vulnerabilidades`

```
StaticAnalyzer → BugHunter → SecurityReviewer → PerformanceProfiler → TestGenerator
```

**MCPs objetivo:**
- `SecurityReviewer` → `semgrep` + `deepwiki`
- `TestGenerator` → `playwright`

**Skills planificadas (Fase 17-A):**
- `static_audit` — auditoría estática con semgrep + checklist OWASP
- `test_plan` — plan de pruebas para un módulo o feature
- `regression_suite` — suite de regresión con playwright

---

## PM pipeline

**Trigger keywords:** `roadmap`, `backlog`, `sprint`, `épicas`, `historias`, `planifica`

```
RequirementsParser → BacklogBuilder → SprintPlanner → RoadmapGenerator
```

**Skills planificadas (Fase 17-A):**
- `roadmap_from_ideas` — convertir lista de ideas en roadmap priorizado
- `sprint_planning` — planning de sprint con estimaciones y dependencias
- `backlog_grooming` — grooming con criterios de aceptación

---

## OFFICE pipeline

**Trigger keywords:** `excel`, `csv`, `pdf`, `word`, `archivo`, `analiza`

```
FileReader → DataAnalyzer → ReportWriter
```

**Skills planificadas (Fase 17-A):**
- `meeting_notes` — procesar grabación/texto → acta + acciones
- `task_extraction` — extraer tareas y owners de documentos
- `email_reply` — redactar respuestas de email en tono definido

---

## MARKETING pipeline

**Trigger keywords:** `marketing`, `campaña`, `copy`, `landing`, `crecimiento`, `adquisición`

```
StrategyAgent → CopyAgent → GrowthAgent → AnalyticsAgent
```

**Skills planificadas (Fase 17-A):**
- `campaign_brief` — brief completo de campaña: objetivo, audiencia, canales
- `audience_persona` — definición de persona con demographics + psicographics
- `multi_channel_post` — post optimizado por canal (X, LinkedIn, Instagram, YT, email)
- `content_calendar` — calendario editorial mensual con temas y formatos

---

## PRODUCT pipeline

**Trigger keywords:** `competidores`, `validar idea`, `feedback`, `feature`, `prioriza`

```
MarketResearcher → FeedbackSynthesizer → FeaturePrioritizer → NudgeDesigner
```

**Skills planificadas (Fase 17-A):**
- `problem_interview` — guía de entrevista de problema + análisis de respuestas
- `feature_brief` — brief de feature: problema, solución, métricas de éxito
- `prioritization_rice` — priorización RICE de backlog con justificación

---

## SECURITY_AUDIT pipeline

**Trigger keywords:** `threat model`, `compliance`, `GDPR`, `vulnerabilidades críticas`

```
ThreatModeler → CodeReviewer → ComplianceChecker
```

**MCPs objetivo:**
- `ThreatModeler` → `semgrep`
- `CodeReviewer` → `deepwiki` + `semgrep`

**Skills planificadas (Fase 17-A):**
- `threat_model` — modelo de amenazas STRIDE para un sistema dado
- `code_security_review` — revisión de seguridad con semgrep + OWASP Top 10
- `compliance_gap` — gap analysis GDPR/CCPA/SOC2

---

## DESIGN pipeline

**Trigger keywords:** `diseña`, `UI`, `componente`, `marca`, `paleta`, `wireframe`

```
UIAgent → UXAgent → BrandAgent → A11yAgent → PromptEngineer
```

**Skills planificadas (Fase 17-A):**
- `ui_review` — revisión de UI contra principios de usabilidad
- `ux_audit` — auditoría UX con heurísticas de Nielsen
- `brand_system` — definición de sistema de marca: colores, tipografía, voz

---

## MCPHub — Mapa de MCPs por agente

```
MCP                  → Agentes que lo usan
─────────────────────────────────────────────
mcp_memory           → TODOS (BaseAgent hooks _before_run/_after_run) ✅ v2.2.2
sequential_thinking  → PlannerAgent, Maestro ✅ v2.2.2
brave_search         → WebScoutAgent ✅ v2.2.2
context7             → CoderAgent ✅ v2.3.0
deepwiki             → CoderAgent, SecurityReviewer
supabase_mcp         → DataAgent, ReportDistributor, DataCollector ✅ v2.3.0
coingecko            → DataAgent, BacktestReader ✅ v2.2.2
okx                  → DataAgent, BacktestReader
github_mcp           → CoderAgent ✅ v2.3.0, GitAgent
semgrep              → SecurityAgent, ThreatModeler, CodeReviewer
playwright           → TestGenerator
slack                → ReportDistributor ✅ v2.3.0
n8n                  → Cualquier agente de automatización
```

---

## Sistema de Skills y `claude.md` por pipeline

> **Estado:** Diseñado en ROADMAP (Fase 17-A). Pendiente implementación.
> Los archivos `skills/` no existen aún en el repo; este apartado es el contrato de diseño.

### Por qué existe este sistema

Los agentes saben **cómo** ejecutar una tarea (Python, MCPs, prompts). Las skills definen
**qué** flujo seguir para resolver tipos de tareas recurrentes. Son archivos `.md` legilbes
por humanos y por el orquestador, sin requerir cambios en el código Python existente.

### Estructura de `skills/`

```text
skills/
  shared/
    schema.md          # Formato canónico de una skill (campos obligatorios + ejemplos)
    safety_guards.md   # Reglas globales: no credenciales, no push sin confirmar, etc.

  <pipeline>/
    claude.md          # Orquestador conceptual del pipeline
    skills/
      <nombre>.md      # Una skill = un flujo reutilizable
```

### Pipelines con skills planificadas (v1)

| Pipeline | claude.md | Skills planificadas (mínimo) |
|---|---|---|
| DEV | ⏳ pendiente | implement_feature, code_review, write_tests, refactor_module |
| RESEARCH | ⏳ pendiente | web_research, competitor_analysis, summarize_sources |
| CONTENT | ⏳ pendiente | longform_to_social, newsletter_issue, landing_copy |
| OFFICE | ⏳ pendiente | meeting_notes, task_extraction, email_reply |
| QA | ⏳ pendiente | static_audit, test_plan, regression_suite |
| PM | ⏳ pendiente | roadmap_from_ideas, sprint_planning, backlog_grooming |
| ANALYTICS | ⏳ pendiente | kpi_report, funnel_analysis, cohort_analysis |
| MARKETING | ⏳ pendiente | campaign_brief, audience_persona, multi_channel_post, content_calendar |
| PRODUCT | ⏳ pendiente | problem_interview, feature_brief, prioritization_rice |
| SECURITY_AUDIT | ⏳ pendiente | threat_model, code_security_review, compliance_gap |
| DESIGN | ⏳ pendiente | ui_review, ux_audit, brand_system |
| TRADING | ❌ excluido v1 | Se incorpora en v2 de Fase 17-A tras validar el esquema |

### Qué define cada `claude.md`

Cada `skills/<pipeline>/claude.md` especifica:
- **Rol del pipeline:** qué problema resuelve y en qué contextos se activa.
- **Agentes disponibles:** lista de `agents/<pipeline>/*` con descripción de cada uno.
- **Skills autorizadas:** lista de skills disponibles para el pipeline.
- **MCPs permitidos:** whitelist sobre los 13 MCPs disponibles.
- **Restricciones de seguridad:** reglas específicas (ej. PM/Marketing no ejecutan código,
  DEV no hace push a main sin confirmación explcita).
- **Política de calidad:** criterios de "done" para el pipeline.

### Qué define cada skill `.md`

Campos canónicos (definidos en `skills/shared/schema.md`):

| Campo | Descripción | Obligatorio |
|---|---|---|
| `name` | Identificador snake_case | Sí |
| `pipeline` | Pipeline dueño de la skill | Sí |
| `version` | Semver de la skill | Sí |
| `description` | Qué resuelve y qué entrega | Sí |
| `required_inputs` | Inputs que el usuario debe proveer | Sí |
| `optional_inputs` | Inputs opcionales con defaults | No |
| `agents_involved` | Agentes participantes y su rol | Sí |
| `tools` | MCPs necesarios | Sí |
| `steps` | Pasos de alto nivel | Sí |
| `output_format` | Estructura esperada del output | Sí |
| `quality_criteria` | Criterios verificables de done | Sí |
| `failure_modes` | Modos de fallo + respuesta | No |
| `examples` | Ejemplos de input/output | Recomendado |

### Integración con Maestro (Fase 17-A, paso 5)

Cuando el skills system esté implementado, Maestro cargará el `claude.md` del
pipeline seleccionado y buscará la skill más afin a la tarea del usuario.
El proceso es solo lectura de archivos `.md`; no hay cambios en `PipelineRouter`
ni en los agentes Python existentes.

```
Maestro.classify(task)
  → pipeline seleccionado
  → carga skills/<pipeline>/claude.md
  → busca skill más afin por keywords/embeddings
  → inyecta skill en AgentContext como "guia de ejecución"
  → ejecuta pipeline normal (PipelineRouter sin cambios)
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
        # 1. Memoria previa recuperada automáticamente por BaseAgent._before_run()
        # 2. Leer inputs del contexto
        # 3. Llamar MCPs: result = await context.mcp_call("mcp_name", "tool", {...})
        # 4. Construir prompt
        # 5. Llamar self.llm(prompt, context)
        # 6. Parsear respuesta
        # 7. Escribir outputs al contexto
        # 8. Retornar contexto (memoria guardada automáticamente por _after_run())
        return context
```

### Llamar un MCP desde un agente

```python
# Verificar disponibilidad antes de llamar
if context.is_mcp_available("brave_search"):
    result = await context.mcp_call(
        "brave_search", "search",
        {"query": "Bitcoin price analysis 2026", "count": 10}
    )
else:
    result = await tools.web_search(query)  # fallback

# PlannerAgent usando sequential_thinking
plan = await context.mcp_call(
    "sequential_thinking", "decompose",
    {"problem": context.task, "steps": 5}
)
```

### Registrar un pipeline nuevo

1. Crear agentes en `agents/<pipeline>/`
2. Añadir entrada en `config.yaml` bajo `pipelines:`
3. Añadir builder en `core/maestro.py` → método `_build_<pipeline>_pipeline()`
4. Añadir keywords en `core/maestro.py` → `_classify_task()`
5. Crear ejemplo en `examples/<pipeline>_example.py`
6. Crear `skills/<pipeline>/claude.md` con agentes, skills y MCPs del pipeline
7. Actualizar `ROADMAP.md` con ítems completados

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
