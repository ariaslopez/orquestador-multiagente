"""APIRouter — Decide qué API LLM usar según el tipo de tarea."""
from __future__ import annotations
import asyncio
import os
import logging
from typing import Optional, List, Dict, Tuple

logger = logging.getLogger(__name__)

# Costo estimado por 1000 tokens (USD) por modelo
COST_PER_1K = {
    "groq": 0.00059,       # llama-3.3-70b: ~$0.59 / 1M tokens
    "gemini": 0.0,         # gemini-2.0-flash: gratis en tier free
    "hyperspace": 0.0,     # local
}


class APIRouter:
    """
    Router inteligente de APIs LLM.

    Estrategia:
    - Tareas de razonamiento complejo → Groq (llama-3.3-70b)
    - Tareas simples / rápidas        → Gemini Flash (gratis)
    - Embeddings / búsqueda local     → Hyperspace local
    - Fallback: Gemini si Groq falla

    complete() retorna Tuple[str, int]: (texto_generado, tokens_usados)
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
        """Retorna el nombre de la API a usar: 'groq' | 'gemini' | 'hyperspace'"""
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
    ) -> Tuple[str, int]:
        """
        Llama a la API más adecuada para el tipo de tarea.
        Retorna (texto_generado, tokens_usados).
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

    async def _call_groq(
        self, messages, system, temperature, max_tokens
    ) -> Tuple[str, int]:
        from .groq_client import GroqClient
        client = GroqClient()
        text = await client.complete(
            messages, system=system, temperature=temperature, max_tokens=max_tokens
        )
        tokens = self._estimate_tokens(messages, text, system)
        return text, tokens

    async def _call_gemini(
        self, messages, system, temperature, max_tokens
    ) -> Tuple[str, int]:
        """
        Llama a Gemini de forma no bloqueante usando run_in_executor.
        google.generativeai no tiene cliente async nativo; sin el
        executor bloquearía el event loop de FastAPI.
        """
        import google.generativeai as genai
        genai.configure(api_key=self.gemini_key)
        model_name = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
        prompt = "\n".join([m["content"] for m in messages])

        def _sync_call():
            model = genai.GenerativeModel(
                model_name=model_name,
                system_instruction=system or "",
            )
            return model.generate_content(prompt)

        # FIX: get_running_loop() en lugar de get_event_loop() (deprecado en Python 3.10+)
        loop = asyncio.get_running_loop()
        response = await loop.run_in_executor(None, _sync_call)

        text = response.text
        try:
            tokens = (
                response.usage_metadata.prompt_token_count
                + response.usage_metadata.candidates_token_count
            )
        except Exception:
            tokens = self._estimate_tokens(messages, text, system)
        return text, tokens

    async def _call_hyperspace(
        self, messages, system, temperature, max_tokens
    ) -> Tuple[str, int]:
        from openai import OpenAI
        client = OpenAI(base_url=self.hyperspace_url, api_key="none")
        full_messages = []
        if system:
            full_messages.append({"role": "system", "content": system})
        full_messages.extend(messages)

        def _sync_call():
            return client.chat.completions.create(
                model="local",
                messages=full_messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )

        # FIX: get_running_loop() en lugar de get_event_loop() (deprecado en Python 3.10+)
        loop = asyncio.get_running_loop()
        response = await loop.run_in_executor(None, _sync_call)

        text = response.choices[0].message.content
        try:
            tokens = response.usage.total_tokens
        except Exception:
            tokens = self._estimate_tokens(messages, text, system)
        return text, tokens

    async def _fallback(
        self, messages, system, temperature, max_tokens, failed_api: str
    ) -> Tuple[str, int]:
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

    @staticmethod
    def _estimate_tokens(messages: list, response_text: str, system: Optional[str]) -> int:
        """Estimación burda: ~1.3 tokens por palabra (promedio en español/inglés)."""
        all_text = " ".join(m.get("content", "") for m in messages)
        if system:
            all_text += " " + system
        all_text += " " + (response_text or "")
        return max(1, int(len(all_text.split()) * 1.3))

    def cost_for_tokens(self, tokens: int, api: str) -> float:
        """Calcula el costo estimado en USD para un número de tokens."""
        rate = COST_PER_1K.get(api, 0.0)
        return round((tokens / 1000) * rate, 6)
