# ARCHITECTURE — CLAW Agent System

> Mapa completo del sistema: 70 agentes del Agency Registry → 12 pipelines de CLAW.
> Este documento es la fuente de verdad para el diseño de las Fases 8–12.

**Versión:** 1.0.0 · **Última actualización:** Abril 2026

---

## Principio de diseño

Los 70 agentes del `AGENT_REGISTRY.md` son **roles especializados**, no pipelines independientes.
Cada pipeline de CLAW es un flujo de trabajo con N agentes colaborando en secuencia o en paralelo.
El resultado es **12 pipelines** que cubren los 70 roles del Registry.

```
AGENT_REGISTRY (70 roles)
         │
         ▼
  12 pipelines CLAW
         │
    ┌────┴────┐
    │ Maestro │  ← Clasifica tarea → pipeline correcto
    └─────────┘
```

---

## Estado de implementación

| Pipeline | Agentes | Estado | Fase |
|----------|---------|--------|------|
| DEV | 6 reales | ✅ Sub-pipeline completo | v1.0.0 |
| RESEARCH | 4 reales (2‖ + 2→) | ✅ Sub-pipeline completo | v1.0.0 |
| CONTENT | 1 macro | ⚠️ Expandir | Fase 8 |
| QA | 1 macro | ⚠️ Expandir | Fase 8 |
| PM | 1 macro | ⚠️ Expandir | Fase 8 |
| OFFICE | 1 macro | ⚠️ Expandir | Fase 8 |
| TRADING | 1 macro | ⚠️ Expandir | Fase 8 |
| DESIGN | — | 🔴 Nuevo | Fase 9 |
| MARKETING | — | 🔴 Nuevo | Fase 9 |
| ANALYTICS | — | 🔴 Nuevo | Fase 9 |
| PRODUCT | — | 🔴 Nuevo | Fase 9 |
| SECURITY_AUDIT | — | 🔴 Nuevo | Fase 9 |

> **Nota:** 6 agentes de Spatial Computing (XR/VisionOS) están registrados pero fuera de scope del roadmap activo.

---

## Pipelines existentes (v1.0.0)

### DEV pipeline

**Trigger keywords:** `crea`, `genera`, `construye`, `proyecto`, `api`, `app`, `código`, `refactor`

```
PlannerAgent → CoderAgent → ReviewerAgent → SecurityAgent → ExecutorAgent → GitAgent
    │               │             │               │               │             │
  plan de        genera         revisa          valida          escribe       hook
  archivos       código         y corrige       seguridad       en disco      Git
  y stack        por archivo
```

**Agentes del Registry mapeados:**
- `engineering-senior-developer` → CoderAgent + ReviewerAgent
- `engineering-backend-architect` → PlannerAgent
- `engineering-security-engineer` → SecurityAgent
- `engineering-devops-automator` → ExecutorAgent + GitAgent
- `engineering-technical-writer` → (documentación en output del PlannerAgent)

**Pendiente:** GitAgent es un stub. La integración real (branch → commit → PR) se implementa en Fase 12 usando `tools/git_ops.py`.

---

### RESEARCH pipeline

**Trigger keywords:** `tesis`, `análisis`, `inversión`, `investigación`, `mercado`, `precio`, `token`

```
             ┌─ WebScoutAgent ─┐
             │  (búsqueda web) │
             │                 ▼
             │           AgentContext
             │                 │
             └─ DataAgent ─────┘
               (datos mercado)  │
                                ▼
                          AnalystAgent
                         (analiza todo)
                                │
                                ▼
                          ThesisAgent
                        (tesis final)
```

**Ejecución:** `parallel_then_sequential` — WebScout y DataAgent corren en paralelo, luego Analyst y Thesis en secuencia.

**Agentes del Registry mapeados:**
- `product-trend-researcher` → WebScoutAgent
- `data-analytics-reporter` + `data-consolidation-agent` → DataAgent
- `engineering-ai-engineer` → AnalystAgent
- `specialized-developer-advocate` → ThesisAgent (output estructurado)

---

## Expansión de pipelines macro (Fase 8)

### CONTENT pipeline (actual: 1 macro → futuro: 5 agentes)

**Trigger keywords:** `contenido`, `tweet`, `hilo`, `post`, `newsletter`, `redacta`, `escribe`

```
TopicAgent → WriterAgent → EditorAgent → BrandAgent → SchedulerAgent
  (tema)      (redacta)    (edita tono)  (verifica    (calendario
                                          marca)       editorial)
```

**Archivos a crear:**
```
agents/content/
├── topic_agent.py       # Selecciona tema según contexto de mercado
├── writer_agent.py      # Redacta contenido con personalidad LLM
├── editor_agent.py      # Edita tono, longitud, hashtags
├── brand_agent.py       # Verifica coherencia de marca
└── scheduler_agent.py   # Propone calendario editorial
```

**Agentes del Registry mapeados:**
- `marketing-twitter-engager` → WriterAgent (personalidades + Twitter-first)
- `marketing-content-creator` → WriterAgent + EditorAgent
- `design-brand-guardian` → BrandAgent
- `marketing-social-media-strategist` → SchedulerAgent
- `design-visual-storyteller` → EditorAgent (narrativa)

---

### QA pipeline (actual: 1 macro → futuro: 5 agentes)

**Trigger keywords:** `audita`, `revisa`, `bugs`, `tests`, `calidad`, `vulnerabilidades`, `coverage`

```
StaticAnalyzer → BugHunter → SecurityReviewer → PerformanceProfiler → TestGenerator
  (linting)      (lógica)     (OWASP Top 10)     (cuellos botella)     (genera tests)
```

**Archivos a crear:**
```
agents/qa/
├── static_analyzer.py       # Linting, tipos, code smells
├── bug_hunter.py            # Bugs lógicos y edge cases
├── security_reviewer.py     # OWASP Top 10, secrets expuestos
├── performance_profiler.py  # N+1 queries, loops costosos
└── test_generator.py        # Genera tests unitarios faltantes
```

**Agentes del Registry mapeados:**
- `testing-reality-checker` → BugHunter (default FAIL hasta evidencia)
- `testing-api-tester` → StaticAnalyzer
- `testing-evidence-collector` → SecurityReviewer
- `testing-performance-benchmarker` → PerformanceProfiler
- `testing-test-results-analyzer` → TestGenerator

---

### PM pipeline (actual: 1 macro → futuro: 4 agentes)

**Trigger keywords:** `roadmap`, `backlog`, `sprint`, `épicas`, `historias`, `planifica`, `milestones`

```
RequirementsParser → BacklogBuilder → SprintPlanner → RoadmapGenerator
  (extrae          (épicas +         (RICE/MoSCoW    (fases +
   requisitos)      historias)        priorización)   milestones)
```

**Archivos a crear:**
```
agents/pm/
├── requirements_parser.py   # Extrae requisitos de descripción libre
├── backlog_builder.py       # Crea backlog estructurado
├── sprint_planner.py        # Priorización con RICE/MoSCoW
└── roadmap_generator.py     # Genera roadmap con fases
```

**Agentes del Registry mapeados:**
- `project-manager-senior` → RequirementsParser + RoadmapGenerator
- `product-sprint-prioritizer` → SprintPlanner
- `project-management-studio-producer` → BacklogBuilder
- `project-management-experiment-tracker` → SprintPlanner (A/B hipótesis)

---

### OFFICE pipeline (actual: 1 macro → futuro: 3 agentes)

**Trigger keywords:** `excel`, `csv`, `pdf`, `word`, `archivo`, `analiza`, `extrae datos`

```
FileReader → DataAnalyzer → ReportWriter
 (extrae      (estadística   (reporte
  datos)       básica)        estructurado)
```

**Archivos a crear:**
```
agents/office/
├── file_reader.py     # Lectura y extracción (usa tools/office_reader.py)
├── data_analyzer.py   # Análisis estadístico básico
└── report_writer.py   # Genera reporte en Markdown/HTML
```

**Agentes del Registry mapeados:**
- `data-consolidation-agent` → FileReader
- `data-analytics-reporter` → DataAnalyzer
- `support-executive-summary-generator` → ReportWriter

---

### TRADING pipeline (actual: 1 macro → futuro: 4 agentes)

**Trigger keywords:** `backtest`, `sharpe`, `drawdown`, `bot`, `estrategia`, `señales`, `trading`

```
BacktestReader → MetricsCalculator → RiskAnalyzer → StrategyAdvisor
  (parsea          (Sharpe, DD,        (exposición,    (recomenda-
   resultados)      win rate)           concentración)  ciones)
```

**Archivos a crear:**
```
agents/trading/
├── backtest_reader.py       # Parsea output de backtests
├── metrics_calculator.py    # Sharpe, drawdown, win rate, Calmar
├── risk_analyzer.py         # Análisis de riesgo y exposición
└── strategy_advisor.py      # Recomendaciones de mejora
```

**Agentes del Registry mapeados:**
- `sales-data-extraction-agent` → BacktestReader (extracción de métricas)
- `data-analytics-reporter` → MetricsCalculator
- `engineering-autonomous-optimization-architect` → StrategyAdvisor

---

## Pipelines nuevos (Fase 9)

### DESIGN pipeline

**Trigger keywords:** `diseña`, `UI`, `componente`, `marca`, `paleta`, `tipografía`, `wireframe`

```
UIAgent → UXAgent → BrandAgent → A11yAgent
(specs     (CSS +    (guías de   (WCAG
 UI)        tokens)   marca)      auditoría)
```

**Agentes del Registry mapeados:**
- `design-ui-designer` → UIAgent
- `design-ux-architect` → UXAgent
- `design-brand-guardian` → BrandAgent
- `testing-accessibility-auditor` → A11yAgent
- `design-whimsy-injector` → UIAgent (micro-interacciones)
- `design-image-prompt-engineer` → (tool auxiliar)

---

### MARKETING pipeline

**Trigger keywords:** `marketing`, `campaña`, `copy`, `landing`, `crecimiento`, `adquisición`, `viral`

```
StrategyAgent → CopyAgent → GrowthAgent → AnalyticsAgent
(estrategia     (copy:       (loops de     (CAC, LTV,
 canales)        ads, emails)  adquisición)  conversion)
```

**Agentes del Registry mapeados:**
- `marketing-social-media-strategist` → StrategyAgent
- `marketing-content-creator` → CopyAgent
- `marketing-growth-hacker` → GrowthAgent
- `support-analytics-reporter` → AnalyticsAgent
- `marketing-reddit-community-builder` → GrowthAgent (comunidad)
- `marketing-app-store-optimizer` → GrowthAgent (ASO)

> **Nota:** Los 3 agentes de mercado chino (Xiaohongshu, WeChat, Zhihu) son variantes del pipeline MARKETING activables por contexto geográfico, no pipelines independientes.

---

### ANALYTICS pipeline

**Trigger keywords:** `reporte`, `KPIs`, `métricas`, `dashboard`, `consolida`, `distribuye`, `ventas`

```
DataCollector → InsightGenerator → ReportDistributor
(consolida       (insights de       (formatea y
 fuentes)         negocio)           distribuye)
```

**Agentes del Registry mapeados:**
- `data-consolidation-agent` → DataCollector
- `data-analytics-reporter` → InsightGenerator
- `report-distribution-agent` → ReportDistributor
- `sales-data-extraction-agent` → DataCollector (ventas)

---

### PRODUCT pipeline

**Trigger keywords:** `competidores`, `validar idea`, `feedback usuarios`, `feature`, `prioriza`, `nudge`

```
MarketResearcher → FeedbackSynthesizer → FeaturePrioritizer → NudgeDesigner
(análisis          (síntesis de          (priorización         (nudges de
 competitivo)       feedback)             data-driven)          comportamiento)
```

**Agentes del Registry mapeados:**
- `product-trend-researcher` → MarketResearcher
- `product-feedback-synthesizer` → FeedbackSynthesizer
- `product-sprint-prioritizer` → FeaturePrioritizer
- `product-behavioral-nudge-engine` → NudgeDesigner

---

### SECURITY_AUDIT pipeline

**Trigger keywords:** `threat model`, `compliance`, `GDPR`, `vulnerabilidades críticas`, `zero-trust`

```
ThreatModeler → CodeReviewer → ComplianceChecker
(modelado de    (OWASP Top 10  (GDPR/CCPA/
 amenazas)       revisión)       API TOS)
```

**Agentes del Registry mapeados:**
- `engineering-security-engineer` → ThreatModeler + CodeReviewer
- `agentic-identity-trust` → ThreatModeler (zero-trust)
- `support-legal-compliance-checker` → ComplianceChecker

---

## Agentes transversales (sin pipeline propio)

Estos agentes del Registry actúan como **capacidades auxiliares** usadas por múltiples pipelines, no como pipelines independientes:

| Agente Registry | Rol en CLAW |
|-----------------|-------------|
| `agents-orchestrator` | Es el Maestro mismo |
| `engineering-rapid-prototyper` | Modo fast del pipeline DEV (`--fast`) |
| `engineering-mobile-app-builder` | Variante del pipeline DEV para móvil |
| `lsp-index-engineer` | Tool auxiliar para indexación semántica de código |
| `specialized-cultural-intelligence-strategist` | Contexto del pipeline MARKETING |
| `specialized-developer-advocate` | Output formatter del pipeline DEV |
| `design-ux-researcher` | Input enricher del pipeline PRODUCT |
| `design-inclusive-visuals-specialist` | Constraint del pipeline DESIGN |
| `project-management-project-shepherd` | Coordinación cross-pipeline (Maestro) |
| `project-management-studio-operations` | Eficiencia operacional (infra) |
| `support-support-responder` | Template responses (out of scope) |
| `support-finance-tracker` | Tool del pipeline ANALYTICS |
| `support-executive-summary-generator` | Output formatter multi-pipeline |
| `testing-tool-evaluator` | Tool del pipeline QA (evalúa stack) |
| `testing-workflow-optimizer` | Tool del pipeline QA (optimiza flujos) |
| XR/Spatial (6 agentes) | Out of scope activo — disponibles si hay caso de uso |

---

## Cobertura final

```
70 agentes del Registry
├── 12 pipelines CLAW               ← 52 agentes activos
│   ├── 7 pipelines v1.0.0
│   └── 5 pipelines nuevos (Fase 9)
├── ~12 agentes transversales       ← capacidades auxiliares
└── 6 agentes Spatial Computing     ← out of scope activo
```

**Cobertura funcional:** ~94% de los 70 agentes tienen lugar en la arquitectura.
El 6% restante (Spatial/XR) está disponible si hay un caso de uso concreto.

---

## Convenciones de implementación

### Estructura de un agente

```python
# agents/<pipeline>/<nombre>_agent.py
from core.base_agent import BaseAgent
from core.context import AgentContext

class NombreAgent(BaseAgent):
    async def run(self, context: AgentContext) -> AgentContext:
        # 1. Leer inputs del contexto
        # 2. Construir prompt
        # 3. Llamar self.llm(prompt, context)
        # 4. Parsear respuesta
        # 5. Escribir outputs al contexto
        # 6. Retornar contexto
        return context
```

### Registrar un pipeline nuevo

1. Crear agentes en `agents/<pipeline>/`
2. Añadir entrada en `config.yaml` bajo `pipelines:`
3. Añadir builder en `core/maestro.py` → método `_build_<pipeline>_pipeline()`
4. Añadir keywords de clasificación en `core/maestro.py` → `_classify_task()`
5. Crear ejemplo en `examples/<pipeline>_example.py`
6. Actualizar `ROADMAP.md` con ítems completados

### Patrones de pipeline

```yaml
# config.yaml — pipeline secuencial
dev:
  type: sequential
  agents: [planner, coder, reviewer, security, executor, git]

# config.yaml — pipeline paralelo + secuencial
research:
  type: parallel_then_sequential
  parallel_agents: [web_scout, data]
  sequential_agents: [analyst, thesis]
```
