"""Configuración global del sistema."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent

# Base de conocimiento
KNOWLEDGE_BASE_DIR = BASE_DIR / "knowledge_base" / "docs"

# LLM Local
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "llama3")

# Embeddings
EMBEDDINGS_MODEL = os.getenv("EMBEDDINGS_MODEL", "all-MiniLM-L6-v2")

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
