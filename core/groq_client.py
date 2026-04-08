"""GroqClient — Cliente LLM para Groq API.

Cambios v2.2.1 (fix audit):
  - Bug E: @retry de tenacity era sincrono — en funciones async nunca
    se ejecutaba el retry real. Reemplazado por retry manual async-native
    con backoff exponencial (mismo comportamiento, compatible con asyncio).
"""
from __future__ import annotations
import asyncio
import os
import logging
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)


class GroqClient:
    """
    Cliente para Groq API con:
    - Retry async-native con backoff exponencial (fix Bug E)
    - Tracking de tokens y costos
    """

    MODELS = {
        "fast":    "llama-3.1-8b-instant",
        "smart":   "llama-3.3-70b-versatile",
        "default": "llama-3.3-70b-versatile",
    }

    COST_PER_1K = {
        "llama-3.1-8b-instant":    0.0001,
        "llama-3.3-70b-versatile": 0.0006,
    }

    # Retry config
    MAX_RETRIES   = 3
    BACKOFF_BASE  = 2   # segundos: 2s → 4s → 8s

    def __init__(self):
        self.api_key       = os.getenv("GROQ_API_KEY", "")
        self.default_model = os.getenv("GROQ_MODEL", self.MODELS["smart"])
        self._client       = None
        self._total_tokens = 0
        self._total_cost   = 0.0

    def _get_client(self):
        if not self._client:
            try:
                from groq import Groq
                self._client = Groq(api_key=self.api_key)
            except ImportError:
                raise RuntimeError("groq no instalado. Ejecuta: pip install groq")
        return self._client

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

        Retry async-native: 3 intentos con backoff 2s → 4s → 8s.
        Bug E fix: tenacity @retry sincrono no funciona con async def.
        """
        if not self.api_key:
            raise ValueError("GROQ_API_KEY no configurada en .env")

        use_model = model or self.default_model
        client    = self._get_client()

        full_messages: List[Dict[str, str]] = []
        if system:
            full_messages.append({"role": "system", "content": system})
        full_messages.extend(messages)

        last_error: Optional[Exception] = None

        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                # Groq SDK es sincrono — correr en executor para no bloquear el event loop
                loop = asyncio.get_running_loop()
                response = await loop.run_in_executor(
                    None,
                    lambda: client.chat.completions.create(
                        model=use_model,
                        messages=full_messages,
                        temperature=temperature,
                        max_tokens=max_tokens,
                    ),
                )

                usage = response.usage
                if usage:
                    tokens = usage.total_tokens
                    cost   = (tokens / 1000) * self.COST_PER_1K.get(use_model, 0.0006)
                    self._total_tokens += tokens
                    self._total_cost   += cost
                    logger.debug(f"Groq: {tokens} tokens, ${cost:.5f} USD (modelo={use_model})")

                return response.choices[0].message.content or ""

            except Exception as e:
                last_error = e
                if attempt < self.MAX_RETRIES:
                    wait = self.BACKOFF_BASE ** attempt  # 2s, 4s, 8s
                    logger.warning(
                        f"GroqClient: intento {attempt}/{self.MAX_RETRIES} falló "
                        f"({e}) → reintentando en {wait}s"
                    )
                    await asyncio.sleep(wait)
                else:
                    logger.error(f"GroqClient: todos los intentos fallaron: {e}")

        raise RuntimeError(
            f"GroqClient: falló después de {self.MAX_RETRIES} intentos. "
            f"Último error: {last_error}"
        )

    async def complete_simple(
        self, prompt: str, model: str = "fast", system: Optional[str] = None
    ) -> str:
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
            "total_tokens":   self._total_tokens,
            "total_cost_usd": round(self._total_cost, 5),
        }
