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
└──────┴──────────卌──────────┴─────────┘
       │          │            │
 ┌─────▼──┐  ┌────▼──┐   ┌─────▼─────┐
 │  DEV   │  │RESEARCH│  │  CONTENT   │  ... (OFFICE/QA/TRADING/PM)
 └─────┬──┘  └────┬───┘   └─────┬─────┘
       └─────────┴───────────┘
                  │
       ┌──────────▼───────────┐
       │   Memoria & Estado  │
       │  (SQLite + Supabase)│
       └─────────────────────┘
```

- `core/maestro.py` decide el tipo de tarea (dev, research, content, etc.) y construye el pipeline adecuado.
- `core/pipeline_router.py` ejecuta los agentes en secuencia o en modo paralelo+secuencial.
- `infrastructure/memory_manager.py` guarda sesiones en SQLite y las sincroniza a Supabase.
- `infrastructure/security_sandbox.py` protege filesystem, comandos y redes según reglas de `config.yaml`.

---

## 🌐 Modos de operación

CLAW soporta dos modos según tu conectividad y preferencias de privacidad:

### Modo Cloud-First (por defecto)

Usa servicios externos para máxima capacidad. Requiere conexión a internet y claves API.

| Componente | Servicio | Costo |
|------------|----------|-------|
| LLM principal | Groq (llama-3.3-70b) | Gratis (con límites) |
| LLM fallback | Gemini 2.0 Flash | Gratis (con límites) |
| Memoria cloud | Supabase | Gratis (tier free) |
| Búsqueda web | DuckDuckGo | Gratis, sin API key |
| Datos crypto | CoinGecko + DeFiLlama | Gratis, sin API key |

**Configuración mínima en `.env`:**
```env
GROQ_API_KEY=tu_clave_groq   # Obligatorio
GEMINI_API_KEY=tu_clave      # Opcional (fallback)
SUPABASE_URL=...             # Opcional (memoria cloud)
SUPABASE_KEY=...             # Opcional (memoria cloud)
```

### Modo Offline (Ollama + ChromaDB)

Usa modelos locales. No requiere internet ni claves API. Ideal para privacidad total o entornos sin conexión.

**Prerrequisitos:**
1. Instalar [Ollama](https://ollama.ai): `ollama pull llama3.1:8b`
2. Las dependencias `sentence-transformers`, `chromadb` y `ollama` ya están en `requirements.txt`

**Configuración en `.env`:**
```env
HYPERSPACE_ENABLED=true
HYPERSPACE_BASE_URL=http://localhost:11434/v1   # Ollama compatible con OpenAI API
GROQ_API_KEY=                                   # Dejar vacío para forzar fallback local
```

**Limitaciones del modo offline:**
- Calidad de respuesta inferior a los modelos cloud de 70B.
- La memoria funciona solo con SQLite local (sin sync a Supabase).
- El pipeline RESEARCH usa DuckDuckGo (requiere red); sin red, solo usa datos de contexto.
- Los pipelines TRADING y RESEARCH con datos crypto requieren acceso a CoinGecko/DeFiLlama.

> **Nota:** El modo offline está funcional pero es un modo secundario. Para uso intensivo de producción, el modo cloud-first ofrece mayor calidad y velocidad.

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
│   ├── code_executor.py     # Ejecución controlada (shell=False)
│   ├── crypto_data.py       # Datos de mercado crypto (CoinGecko/DeFiLlama)
│   ├── safe_filesystem.py   # Acceso a disco seguro
│   └── git_ops.py           # Integración GitHub (PyGithub)
├── ui/
│   ├── server.py            # FastAPI + WebSockets
│   └── index.html           # Dashboard HTML Tailwind
├── examples/
│   ├── dev_example.py
│   ├── research_example.py
│   ├── content_example.py
│   ├── office_example.py
│   ├── qa_example.py
│   ├── trading_example.py
│   └── pm_example.py
├── tests/                   # Tests unitarios + integración
├── config.yaml              # Configuración global y pipelines
├── main.py                  # Punto de entrada CLI
├── requirements.txt
├── .env.example
├── CONTRIBUTING.md
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
# Edita .env con tus claves (Groq obligatorio, resto opcional)

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

# Clasificación automática
python main.py --task "Audita este modulo buscando vulnerabilidades"  # detecta QA
```

### UI web (Dashboard)

```bash
python main.py --ui
# Abre: http://127.0.0.1:8000
```

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
- **`shell=False`** en todas las ejecuciones de subprocesos para prevenir shell injection.
- Sandbox de filesystem y comandos en `infrastructure/security_sandbox.py`.
- Logs de auditoría en `infrastructure/audit_logger.py` y `logs/`.
- `GITHUB_CONFIRM_BEFORE_PUSH=true` por defecto — el sistema nunca hace push sin confirmación.
- `.env` creado con permisos `600` (solo el usuario propietario puede leerlo).

---

## ⚠️ Riesgos conocidos

Esta sección documenta explícitamente los límites de seguridad actuales. La transparencia sobre el riesgo es más segura que ignorarlo.

### El pipeline DEV ejecuta código en tu máquina host

Cuando usas `--type dev`, el `ExecutorAgent` escribe archivos en disco y puede ejecutar comandos (`pip install`, `pytest`, etc.) en el mismo proceso del sistema operativo. El sandbox de CLAW actua como **primera línea de defensa**, no como aislamiento total:

- ✅ Bloquea patrones peligrosos conocidos (`rm -rf`, `DROP TABLE`, pipe-to-bash, etc.)
- ✅ Valida comandos contra lista blanca
- ✅ Usa `shell=False` para prevenir shell injection básica
- ⚠️ **No es un sandbox a nivel OS** — un modelo que genere `python -c "import os; os.system(...)"` puede ejecutar código arbitrario si pasa la whitelist

**Mitigación recomendada para producción:** Ejecutar CLAW dentro de un container Docker efimero por tarea. Esto está en el ROADMAP como siguiente paso de seguridad.

**Nivel de riesgo actual:** Bajo para uso personal en PC de desarrollo. Medio-alto si expones el endpoint `/api/task` a internet sin autenticación.

### Prompt injection en tareas de entrada libre

El Maestro clasifica y procesa texto libre del usuario. Un input malicioso diseñado para manipular el LLM (prompt injection) podría en teoría afectar el comportamiento del pipeline. No hay un filtro de sanitización de input implementado actualmente.

**Mitigación:** Limitar el acceso a la UI/API a usuarios de confianza mientras no haya autenticación en `/api/task`.

### `.env` contiene credenciales en texto plano

El archivo `.env` almacena API keys en texto plano. `setup.py` aplica permisos `600` (solo el usuario propietario puede leer el archivo en Unix/Linux/Mac). En Windows, los permisos de archivo tienen semantíca diferente.

**Mitigación:** Nunca hacer commit del `.env` (ya está en `.gitignore`). Para producción en servidor, usar variables de entorno del sistema o un secrets manager (AWS Secrets Manager, Vault, etc.).

---

## 🧪 Tests y ejemplos

- Tests unitarios y de integración en `tests/` cubren core, agents, infrastructure, tools y pipelines DEV/RESEARCH.
- Directorio `examples/` contiene scripts listos para correr cada pipeline.

```bash
# Correr todos los tests (sin API keys, sin red)
pytest tests/ -v

python examples/dev_example.py
python examples/research_example.py
```

---

## 📌 Estado del proyecto

- Este repo refleja la **versión 1.0.0** del orquestador multi-agente.
- Cualquier funcionalidad adicional (Docker, GitHubPR automático, paralelo avanzado, etc.) está documentada como **deuda técnica** en `ROADMAP.md`.
- Para contribuir, lee `CONTRIBUTING.md`.

Si ves alguna inconsistencia entre el código y la documentación, el código y el ROADMAP tienen prioridad como fuente de verdad.
