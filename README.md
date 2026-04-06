# 🤖 CLAW Agent System — Orquestador Multi-Agente

**Versión:** 1.0.0

Sistema de inteligencia artificial multi-agente diseñado para automatizar trabajo de desarrollo, investigación y análisis en el ecosistema crypto.

- 7 pipelines especializados: DEV, RESEARCH, CONTENT, OFFICE, QA, TRADING, PM.
- Orquestador central (Maestro) que decide qué agentes ejecutar y en qué orden.
- Memoria local + Supabase para recordar sesiones anteriores.
- UI web opcional vía FastAPI + WebSockets.

> Este repositorio implementa la arquitectura descrita en el documento PDF del CLAW Agent System. Toda la estructura y los agentes descritos allí están construidos o registrados como deuda técnica explícita.

---

## 🧠 Arquitectura de alto nivel

```text
┌─────────────────────────────────────────┐
│              MAESTRO (LLM)             │
│  Clasifica tarea → selecciona pipeline │
└──────┬──────────┬────────────┬─────────┘
       │          │            │
 ┌─────▼──┐  ┌────▼──┐   ┌─────▼──────┐
 │  DEV   │  │RESEARCH│  │  CONTENT   │  ... (OFFICE/QA/TRADING/PM)
 └─────┬──┘  └────┬───┘   └─────┬──────┘
       └──────────┴─────────────┘
                  │
       ┌──────────▼──────────┐
       │   Memoria & Estado  │
       │  (SQLite + Supabase)│
       └─────────────────────┘
```

- `core/maestro.py` decide el tipo de tarea (dev, research, content, etc.) y construye el pipeline adecuado.
- `core/pipeline_router.py` ejecuta los agentes en secuencia o en modo paralelo+secuencial.
- `infrastructure/memory_manager.py` guarda sesiones en SQLite y las sincroniza a Supabase.
- `infrastructure/security_sandbox.py` protege filesystem, comandos y redes según reglas de `config.yaml`.

---

## 📁 Estructura del proyecto

```text
orquestador-multiagente/
├── core/
│   ├── base_agent.py        # Contrato base de todos los agentes
│   ├── context.py           # Estado compartido entre agentes
│   ├── maestro.py           # Orquestador central (Maestro)
│   ├── api_router.py        # Router de APIs LLM (Groq, Gemini, Hyperspace)
│   ├── pipeline.py          # Definición de pipeline lógico
│   └── pipeline_router.py   # Ejecutor secuencial / paralelo+secuencial
├── agents/
│   ├── dev/
│   │   ├── planner_agent.py   # Árbol de archivos + stack
│   │   ├── coder_agent.py     # Genera código archivo por archivo
│   │   ├── reviewer_agent.py  # Revisa y corrige código
│   │   ├── security_agent.py  # Chequeos de seguridad básicos
│   │   └── executor_agent.py  # Escribe en disco e instala deps
│   ├── research/
│   │   ├── webscout_agent.py  # Búsqueda web DuckDuckGo
│   │   ├── data_agent.py      # Datos de mercado (CryptoDataTool)
│   │   ├── analyst_agent.py   # Analiza datos web + mercado
│   │   └── thesis_agent.py    # Genera tesis de inversión estructurada
│   ├── personas/
│   │   └── personas_registry.py # 61 personalidades de agency-agents
│   ├── content_agent.py       # Contenido crypto con personalidades
│   ├── office_agent.py        # Lectura/analítica de Excel, PDF, Word, CSV
│   ├── qa_agent.py            # Auditoría de código
│   ├── trading_agent.py       # Analytics de bots/backtests
│   └── pm_agent.py            # Backlog, roadmap, sprints
├── infrastructure/
│   ├── memory_manager.py    # SQLite + Supabase
│   ├── security_layer.py    # Reglas de seguridad de alto nivel
│   ├── security_sandbox.py  # Sandbox de filesystem/comandos
│   ├── audit_logger.py      # Logs estructurados
│   ├── state_manager.py     # Manejo de estado de sesión
│   └── output_manager.py    # Manejo de output y carpetas
├── tools/
│   ├── web_search.py        # Búsqueda web por DuckDuckGo
│   ├── file_ops.py          # Utilidades de archivos
│   ├── office_reader.py     # Lectura de Office/PDF
│   ├── code_executor.py     # Ejecución controlada de código
│   ├── crypto_data.py       # Datos de mercado crypto (CoinGecko/DeFiLlama)
│   ├── safe_filesystem.py   # Acceso a disco seguro
│   └── git_ops.py           # Integración GitHub (PyGithub)
├── ui/
│   ├── server.py            # FastAPI + WebSockets
│   └── index.html           # Dashboard HTML Tailwind
├── examples/
│   ├── dev_example.py       # Ejemplo Dev pipeline
│   ├── research_example.py  # Ejemplo Research
│   ├── content_example.py   # Ejemplo Content
│   ├── office_example.py    # Ejemplo Office
│   ├── qa_example.py        # Ejemplo QA
│   ├── trading_example.py   # Ejemplo Trading
│   └── pm_example.py        # Ejemplo PM
├── tests/                   # Tests unitarios básicos
├── config.yaml              # Configuración global y pipelines
├── main.py                  # Punto de entrada CLI
├── requirements.txt
├── .env.example
└── ROADMAP.md
```

---

## 🔀 Pipelines disponibles

Los pipelines se configuran en `config.yaml` y se ejecutan vía `core/maestro.py`.

- **DEV** (`--type dev`): genera proyectos de software completos.
- **RESEARCH** (`--type research`): tesis de inversión con datos web + mercado.
- **CONTENT** (`--type content`): contenido crypto estructurado (hilos, posts, newsletters).
- **OFFICE** (`--type office`): analiza archivos Excel, CSV, Word, PDF.
- **QA** (`--type qa`): auditoría de código (bugs, seguridad, performance, tests).
- **TRADING** (`--type trading`): analytics de bots y backtests.
- **PM** (`--type pm`): backlog y sprints desde una descripción de proyecto.

La clasificación automática sin `--type` se basa en keywords y, en caso de ambigüedad, en un LLM de Groq.

---

## 🚀 Instalación y uso básico

```bash
# Clonar repo
git clone https://github.com/ariaslopez/orquestador-multiagente
cd orquestador-multiagente

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env
# Edita .env con tus claves (Groq, Supabase, GitHub opcional)

# Setup inicial
python setup.py

# Verificación del sistema
python main.py --doctor
```

### Ejecutar tareas desde CLI

```bash
# Generar un proyecto (pipeline DEV)
python main.py --task "Crea una API REST en FastAPI para gestionar senales de trading" --type dev

# Tesis de inversión (pipeline RESEARCH)
python main.py --task "Tesis de inversion para Solana Q2 2026" --type research

# Analizar un Excel (pipeline OFFICE)
python main.py --task "Analiza este backtest" --type office --file data/backtest_sample.xlsx

# Usar clasificación automática
python main.py --task "Audita este modulo buscando vulnerabilidades"  # detecta QA
```

### UI web (Dashboard)

```bash
python main.py --ui
# Abre: http://127.0.0.1:8000
```

El dashboard permite:
- Escribir una tarea en lenguaje natural.
- Seleccionar un pipeline (o dejar auto).
- Ver el output, tokens y costo estimado.

---

## 💾 Memoria y estado

- **Local**: SQLite (`./data/claw_memory.db`) para sesiones recientes.
- **Nube**: Supabase opcional para sincronizar historial entre máquinas.
- `infrastructure/memory_manager.py` expone métodos para guardar y recuperar sesiones.

Esto permite que:
- El sistema recuerde tesis anteriores sobre un mismo activo.
- Evite duplicar proyectos ya generados.
- Continúe trabajo interrumpido desde el último checkpoint.

---

## 🔐 Seguridad

Implementada en múltiples capas:

- Paths protegidos (no toca `C:/Windows`, `/etc`, etc.) definidos en `config.yaml`.
- Lista blanca de comandos permitidos (`pip install`, `pytest`, `git`, etc.).
- Bloqueo de patrones peligrosos (`rm -rf`, `DROP TABLE`, etc.).
- Sandbox de filesystem y comandos en `infrastructure/security_sandbox.py`.
- Logs detallados de operaciones en `infrastructure/audit_logger.py` y `logs/`.

---

## 🧪 Tests y ejemplos

- Tests unitarios básicos en `tests/` cubren core, agents, infrastructure y tools.
- Directorio `examples/` contiene scripts listos para correr cada pipeline.

Ejemplo rápido:

```bash
python examples/dev_example.py
python examples/research_example.py
python examples/content_example.py
```

---

## 📌 Estado del proyecto

- Este repo refleja la **versión 1.0.0** del orquestador multi-agente descrito en el PDF.
- Cualquier funcionalidad adicional (plugin Hyperspace, Docker, GitHubPR automático, etc.) está documentada como **deuda técnica** en `ROADMAP.md`.

Si ves alguna inconsistencia entre el código y el documento, el código y el ROADMAP tienen prioridad como fuente de verdad de la implementación actual.
