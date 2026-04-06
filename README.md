# 🤖 Orquestador Multi-Agente (Local Offline)

Sistema de inteligencia artificial multi-agente diseñado para funcionar **100% en ambiente local sin conexión a internet**.

Cada agente se especializa en una tarea específica (documentación, análisis de código, generación, etc.) y se comunican entre sí a través del orquestador central.

---

## 🏗️ Arquitectura

```
┌─────────────────────────────────────────┐
│          ORQUESTADOR (Maestro)          │
│    Recibe tarea → decide el flujo       │
└──────┬──────────┬────────────┬──────────┘
       │          │            │
 ┌─────▼──┐  ┌────▼──┐  ┌─────▼──────┐
 │ Agente │  │Agente │  │  Agente    │
 │  Docs  │  │Código │  │ Respuesta  │
 └─────┬──┘  └────┬──┘  └─────┬──────┘
       └──────────┴────────────┘
                  │
       ┌──────────▼──────────┐
       │   Estado Compartido │
       │    (memoria local)  │
       └─────────────────────┘
```

## 📁 Estructura del Proyecto

```
orquestador-multiagente/
├── core/
│   ├── base_agent.py          # Contrato base de todos los agentes
│   ├── orchestrator.py        # Orquestador central
│   ├── context.py             # Estado compartido entre agentes
│   └── pipeline.py            # Configuración de pipelines
├── agents/
│   ├── doc_agent.py           # Agente de documentación
│   ├── code_agent.py          # Agente de análisis de código
│   ├── search_agent.py        # Agente de búsqueda en docs locales
│   ├── response_agent.py      # Agente de síntesis de respuesta final
│   └── language_agent.py      # Agente de detección de lenguaje
├── knowledge_base/
│   ├── docs/                  # Documentación local por lenguaje
│   │   ├── python/
│   │   ├── javascript/
│   │   ├── java/
│   │   └── ...
│   └── index.json             # Índice de la base de conocimiento
├── config/
│   ├── settings.py            # Configuración global
│   └── pipelines.yaml         # Definición de pipelines
├── tools/
│   ├── file_loader.py         # Cargador de archivos locales
│   ├── text_splitter.py       # Splitter de documentos
│   └── embeddings_local.py    # Embeddings locales (sentence-transformers)
├── main.py                    # Punto de entrada
├── requirements.txt
└── .env.example
```

## 🚀 Instalación

```bash
git clone https://github.com/ariaslopez/orquestador-multiagente
cd orquestador-multiagente
pip install -r requirements.txt
cp .env.example .env
python main.py
```

## ⚙️ Requisitos

- Python 3.10+
- Ollama (LLM local)
- sentence-transformers (embeddings locales)
- chromadb (vector store local)

## 🔌 Sin Internet

Este sistema funciona completamente offline:
- LLM local via **Ollama** (llama3, mistral, etc.)
- Embeddings con **sentence-transformers** (modelo descargado localmente)
- Vector store con **ChromaDB** (persistencia local)
- Documentación cargada desde archivos locales
