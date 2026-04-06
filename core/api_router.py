"""APIRouter — Decide qué API LLM usar según el tipo de tarea."""
from __future__ import annotations
import os
import logging
from typing import Optional, List, Dict

logger = logging.getLogger(__name__)


class APIRouter:
    """
    Router inteligente de APIs LLM.

    Estrategia:
    - Tareas de razonamiento complejo → Groq (llama-3.3-70b)
    - Tareas simples / rápidas → Gemini Flash (gratis)
    - Embeddings / búsqueda local → Hyperspace local
    - Fallback: Gemini si Groq falla
    """

    REASONING_TASKS = {"planning", "analysis", "review", "research", "thesis", "coding"}
    FAST_TASKS = {"formatting", "content", "summary", "extraction", "classification"}
    LOCAL_TASKS = {"embeddings", "similarity", "search"}

    def __init__(self):
        self.groq_key = os.getenv("GROQ_API_KEY", "")
        self.gemini_key = os.getenv("GEMINI_API_KEY", "")
        self.hyperspace_url = os.getenv("HYPERSPACE_BASE_URL", "http://localhost:8080/v1")
        self.hyperspace_enabled = os.getenv("HYPERSPACE_ENABLED", "false").lower() == "true"
        self._strategy = os.getenv("API_STRATEGY", "smart")

    def select_api(self, task_type: str) -> str:
        """
        Retorna el nombre de la API a usar: 'groq' | 'gemini' | 'hyperspace'
        """
        if self._strategy == "groq_only":
            return "groq"
        if self._strategy == "gemini_only":
            return "gemini"
        if self._strategy == "local_only":
            return "hyperspace"

        # Smart routing
        if task_type in self.LOCAL_TASKS and self.hyperspace_enabled:
            return "hyperspace"
        if task_type in self.FAST_TASKS and self.gemini_key:
            return "gemini"
        if task_type in self.REASONING_TASKS and self.groq_key:
            return "groq"

        # Fallback
        if self.groq_key:
            return "groq"
        if self.gemini_key:
            return "gemini"
        return "hyperspace"

    async def complete(
        self,
        messages: List[Dict[str, str]],
        task_type: str = "reasoning",
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> str:
        """
        Llama a la API más adecuada para el tipo de tarea.
        Si la primaria falla, hace fallback automático.
        """
        api = self.select_api(task_type)
        logger.info(f"APIRouter: {task_type} → {api}")

        try:
            if api == "groq":
                return await self._call_groq(messages, system, temperature, max_tokens)
            elif api == "gemini":
                return await self._call_gemini(messages, system, temperature, max_tokens)
            else:
                return await self._call_hyperspace(messages, system, temperature, max_tokens)
        except Exception as e:
            logger.warning(f"APIRouter: {api} falló ({e}), intentando fallback...")
            return await self._fallback(messages, system, temperature, max_tokens, failed_api=api)

    async def _call_groq(self, messages, system, temperature, max_tokens) -> str:
        from .groq_client import GroqClient
        client = GroqClient()
        return await client.complete(messages, system=system, temperature=temperature, max_tokens=max_tokens)

    async def _call_gemini(self, messages, system, temperature, max_tokens) -> str:
        import google.generativeai as genai
        genai.configure(api_key=self.gemini_key)
        model = genai.GenerativeModel(
            model_name=os.getenv("GEMINI_MODEL", "gemini-2.0-flash"),
            system_instruction=system or "",
        )
        prompt = "\n".join([m["content"] for m in messages])
        response = model.generate_content(prompt)
        return response.text

    async def _call_hyperspace(self, messages, system, temperature, max_tokens) -> str:
        from openai import OpenAI
        client = OpenAI(base_url=self.hyperspace_url, api_key="none")
        full_messages = []
        if system:
            full_messages.append({"role": "system", "content": system})
        full_messages.extend(messages)
        response = client.chat.completions.create(
            model="local",
            messages=full_messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content

    async def _fallback(self, messages, system, temperature, max_tokens, failed_api: str) -> str:
        """Intenta las APIs restantes en orden de prioridad."""
        apis = ["groq", "gemini", "hyperspace"]
        apis.remove(failed_api)
        for api in apis:
            try:
                if api == "groq" and self.groq_key:
                    return await self._call_groq(messages, system, temperature, max_tokens)
                elif api == "gemini" and self.gemini_key:
                    return await self._call_gemini(messages, system, temperature, max_tokens)
                elif api == "hyperspace" and self.hyperspace_enabled:
                    return await self._call_hyperspace(messages, system, temperature, max_tokens)
            except Exception as e:
                logger.warning(f"Fallback {api} también falló: {e}")
        raise RuntimeError("Todas las APIs fallaron. Verifica tus API keys en .env")
