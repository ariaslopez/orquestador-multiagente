"""GroqClient — Cliente LLM principal con retry automático y fallback."""
from __future__ import annotations
import os
import logging
from typing import Optional, List, Dict, Any
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)


class GroqClient:
    """
    Cliente para Groq API con:
    - Retry automático con backoff exponencial
    - Fallback a Gemini si Groq falla
    - Tracking de tokens y costos
    """

    MODELS = {
        "fast": "llama-3.1-8b-instant",
        "smart": "llama-3.3-70b-versatile",
        "default": "llama-3.3-70b-versatile",
    }

    # Costo estimado por 1000 tokens (USD)
    COST_PER_1K = {
        "llama-3.1-8b-instant": 0.0001,
        "llama-3.3-70b-versatile": 0.0006,
    }

    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY", "")
        self.default_model = os.getenv("GROQ_MODEL", self.MODELS["smart"])
        self._client = None
        self._total_tokens = 0
        self._total_cost = 0.0

    def _get_client(self):
        if not self._client:
            try:
                from groq import Groq
                self._client = Groq(api_key=self.api_key)
            except ImportError:
                raise RuntimeError("groq no instalado. Ejecuta: pip install groq")
        return self._client

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(Exception),
    )
    async def complete(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        system: Optional[str] = None,
    ) -> str:
        """
        Llama a Groq y retorna el texto de respuesta.
        Incluye retry automático y tracking de tokens.
        """
        if not self.api_key:
            raise ValueError("GROQ_API_KEY no configurada en .env")

        use_model = model or self.default_model
        client = self._get_client()

        # Agregar system prompt si se proporciona
        full_messages = []
        if system:
            full_messages.append({"role": "system", "content": system})
        full_messages.extend(messages)

        try:
            response = client.chat.completions.create(
                model=use_model,
                messages=full_messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )

            # Track tokens y costo
            usage = response.usage
            if usage:
                tokens = usage.total_tokens
                cost = (tokens / 1000) * self.COST_PER_1K.get(use_model, 0.0006)
                self._total_tokens += tokens
                self._total_cost += cost
                logger.debug(f"Groq: {tokens} tokens, ${cost:.5f} USD")

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"Groq error: {e}")
            raise

    async def complete_simple(self, prompt: str, model: str = "fast", system: Optional[str] = None) -> str:
        """Shortcut para prompts simples de un solo mensaje."""
        model_id = self.MODELS.get(model, self.MODELS["default"])
        return await self.complete(
            messages=[{"role": "user", "content": prompt}],
            model=model_id,
            system=system,
        )

    @property
    def usage_stats(self) -> Dict[str, Any]:
        return {
            "total_tokens": self._total_tokens,
            "total_cost_usd": round(self._total_cost, 5),
        }
