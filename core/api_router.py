"""APIRouter — Local-first LLM strategy con exponential backoff y CoT.

Cambios v2.2.1 (fix audit):
  - Bug C fix: complete() ahora retorna Tuple[str, int, str]:
    (texto, tokens, provider_used). El tercer valor es el provider
    REAL que respondió (puede ser el fallback, no el primario).
    BaseAgent.llm() usa este valor para calcular costos correctamente.

Estrategia de providers (en orden de prioridad):
  1. Ollama local     → gratis, offline, 0 latencia de red
  2. Groq             → gratis (14,400 tok/min), ultra rápido
  3. Gemini Flash     → gratis (1M tok/día), fallback fiable
  4. Hyperspace       → fallback legacy local
"""
from __future__ import annotations
import asyncio
import os
import re
import logging
from typing import Optional, List, Dict, Tuple

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Costo estimado por 1000 tokens (USD)
# ---------------------------------------------------------------------------
COST_PER_1K: Dict[str, float] = {
    "ollama":     0.0,
    "groq":       0.00059,
    "gemini":     0.0,
    "hyperspace": 0.0,
}

# ---------------------------------------------------------------------------
# Límites reales de contexto por provider (tokens)
# ---------------------------------------------------------------------------
CLOUD_CONTEXT_LIMITS: Dict[str, int] = {
    "ollama":       32_768,
    "groq":        131_072,
    "gemini":    1_000_000,
    "hyperspace":    8_192,
}

FREE_TIER_LIMITS = {
    "groq":   {"tokens_per_minute": 14_400, "requests_per_minute": 30},
    "gemini": {"tokens_per_day": 1_000_000, "requests_per_minute": 15},
}

OLLAMA_PROFILES = {
    "cpu_8gb":  {"model": "llama3.2:3b-q4_K_M",           "gpu_layers": 0,  "context": 8_192},
    "cpu_16gb": {"model": "qwen2.5-coder:7b-q4_K_M",      "gpu_layers": 0,  "context": 32_768},
    "cpu_24gb": {"model": "qwen2.5-coder:7b-q4_K_M",      "gpu_layers": 4,  "context": 32_768},
    "gpu_8gb":  {"model": "deepseek-coder-v2:16b-q4_K_M",  "gpu_layers": 33, "context": 65_536},
    "gpu_12gb": {"model": "qwen2.5-coder:14b-q4_K_M",      "gpu_layers": 43, "context": 65_536},
    "gpu_16gb": {"model": "qwen2.5-coder:14b-q4_K_M",      "gpu_layers": 43, "context": 128_000},
    "gpu_24gb": {"model": "qwen2.5-coder:32b-q4_K_M",      "gpu_layers": 65, "context": 128_000},
}


class APIRouter:
    """
    Router inteligente de APIs LLM con estrategia local-first.

    complete() retorna Tuple[str, int, str]:
      (texto_generado, tokens_usados, provider_usado)

    El tercer elemento es el provider REAL que respondió — puede ser
    diferente al primario si hubo fallback.
    """

    CLOUD_PREFERRED_TASKS = {
        "research", "thesis", "analysis", "security_audit",
        "planning", "reasoning",
    }
    LOCAL_PREFERRED_TASKS = {
        "coding", "formatting", "summary", "extraction",
        "classification", "embeddings", "similarity",
        "review", "content", "office", "qa", "pm",
        "trading", "analytics", "marketing", "product", "design",
    }
    REASONING_TASKS = {
        "classification", "planning", "security_audit",
        "research", "analysis", "reasoning",
    }

    def __init__(self):
        self.groq_key   = os.getenv("GROQ_API_KEY", "")
        self.gemini_key = os.getenv("GEMINI_API_KEY", "")

        self.ollama_url     = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
        self.ollama_enabled = os.getenv("OLLAMA_ENABLED", "false").lower() == "true"
        self.hw_profile     = os.getenv("OLLAMA_HW_PROFILE", "cpu_24gb")
        self._ollama_cfg    = OLLAMA_PROFILES.get(self.hw_profile, OLLAMA_PROFILES["cpu_24gb"])
        self.ollama_model   = os.getenv("OLLAMA_MODEL", self._ollama_cfg["model"])
        self.ollama_layers  = int(os.getenv("LOCAL_GPU_LAYERS", str(self._ollama_cfg["gpu_layers"])))
        self.ollama_context = int(os.getenv("LOCAL_CONTEXT_SIZE", str(self._ollama_cfg["context"])))

        self.hyperspace_url     = os.getenv("HYPERSPACE_BASE_URL", "http://localhost:8080/v1")
        self.hyperspace_enabled = os.getenv("HYPERSPACE_ENABLED", "false").lower() == "true"

        self._strategy = os.getenv("API_STRATEGY", "local_first")

        logger.info(
            f"APIRouter init | strategy={self._strategy} | "
            f"ollama={'ON '+self.ollama_model if self.ollama_enabled else 'OFF'} | "
            f"hw_profile={self.hw_profile} | gpu_layers={self.ollama_layers}"
        )

    # ------------------------------------------------------------------
    # Selección de provider
    # ------------------------------------------------------------------

    def select_provider(self, task_type: str, estimated_tokens: int = 0) -> str:
        """Retorna el provider a usar: 'ollama' | 'groq' | 'gemini' | 'hyperspace'"""
        if self._strategy == "local_only":
            return "ollama" if self.ollama_enabled else "hyperspace"
        if self._strategy == "groq_only":
            return "groq"
        if self._strategy == "gemini_only":
            return "gemini"
        if self._strategy == "cloud_only":
            return "groq" if self.groq_key else "gemini"

        if self.ollama_enabled:
            if task_type in self.CLOUD_PREFERRED_TASKS and (self.groq_key or self.gemini_key):
                return "groq" if self.groq_key else "gemini"
            if estimated_tokens > self.ollama_context * 0.85:
                logger.info(
                    f"APIRouter: {estimated_tokens} tokens > 85% ctx local "
                    f"({self.ollama_context}) → escalando a cloud"
                )
                if estimated_tokens <= CLOUD_CONTEXT_LIMITS.get("groq", 0) and self.groq_key:
                    return "groq"
                if self.gemini_key:
                    return "gemini"
            return "ollama"

        if self.groq_key:
            return "groq"
        if self.gemini_key:
            return "gemini"
        return "hyperspace"

    # ------------------------------------------------------------------
    # Punto de entrada principal — retorna (text, tokens, provider_used)
    # ------------------------------------------------------------------

    async def complete(
        self,
        messages: List[Dict[str, str]],
        task_type: str = "coding",
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> Tuple[str, int, str]:
        """
        Genera completación con el provider óptimo.

        Retorna (texto_generado, tokens_usados, provider_usado).
        El tercer elemento es el provider REAL post-fallback (Bug C fix).
        """
        estimated = self._estimate_tokens(messages, "", system, task_type)
        provider  = self.select_provider(task_type, estimated)
        logger.info(
            f"APIRouter: task_type={task_type} → provider={provider} "
            f"(~{estimated} tokens estimados)"
        )

        try:
            text, tokens = await self._call(provider, messages, system, temperature, max_tokens)
            return text, tokens, provider
        except Exception as e:
            logger.warning(f"APIRouter: {provider} falló ({e}), iniciando fallback chain...")
            return await self._fallback_chain(
                messages, system, temperature, max_tokens, failed=provider
            )

    # ------------------------------------------------------------------
    # Llamadas por provider — retornan (text, tokens)
    # ------------------------------------------------------------------

    async def _call(
        self, provider: str, messages, system, temperature, max_tokens
    ) -> Tuple[str, int]:
        if provider == "ollama":
            return await self._call_ollama(messages, system, temperature, max_tokens)
        elif provider == "groq":
            return await self._call_groq(messages, system, temperature, max_tokens)
        elif provider == "gemini":
            return await self._call_gemini(messages, system, temperature, max_tokens)
        else:
            return await self._call_hyperspace(messages, system, temperature, max_tokens)

    async def _call_ollama(self, messages, system, temperature, max_tokens) -> Tuple[str, int]:
        from openai import OpenAI
        client = OpenAI(base_url=self.ollama_url, api_key="ollama")

        full_messages = []
        if system:
            full_messages.append({"role": "system", "content": system})
        full_messages.extend(messages)

        options = {"num_gpu": self.ollama_layers} if self.ollama_layers > 0 else {}

        loop = asyncio.get_running_loop()
        response = await loop.run_in_executor(
            None,
            lambda: client.chat.completions.create(
                model=self.ollama_model,
                messages=full_messages,
                temperature=temperature,
                max_tokens=max_tokens,
                extra_body={"options": options} if options else {},
            ),
        )

        text = response.choices[0].message.content or ""
        text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
        try:
            tokens = response.usage.total_tokens
        except Exception:
            tokens = self._estimate_tokens(messages, text, system)
        return text, tokens

    async def _call_groq(self, messages, system, temperature, max_tokens) -> Tuple[str, int]:
        from .groq_client import GroqClient
        client = GroqClient()
        text   = await client.complete(
            messages, system=system, temperature=temperature, max_tokens=max_tokens
        )
        tokens = self._estimate_tokens(messages, text, system)
        return text, tokens

    async def _call_gemini(self, messages, system, temperature, max_tokens) -> Tuple[str, int]:
        import google.generativeai as genai
        genai.configure(api_key=self.gemini_key)
        model_name = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
        prompt     = "\n".join([m["content"] for m in messages])

        loop = asyncio.get_running_loop()
        response = await loop.run_in_executor(
            None,
            lambda: genai.GenerativeModel(
                model_name=model_name,
                system_instruction=system or "",
            ).generate_content(prompt),
        )
        text = response.text
        try:
            tokens = (
                response.usage_metadata.prompt_token_count
                + response.usage_metadata.candidates_token_count
            )
        except Exception:
            tokens = self._estimate_tokens(messages, text, system)
        return text, tokens

    async def _call_hyperspace(self, messages, system, temperature, max_tokens) -> Tuple[str, int]:
        from openai import OpenAI
        client = OpenAI(base_url=self.hyperspace_url, api_key="none")
        full_messages = []
        if system:
            full_messages.append({"role": "system", "content": system})
        full_messages.extend(messages)

        loop = asyncio.get_running_loop()
        response = await loop.run_in_executor(
            None,
            lambda: client.chat.completions.create(
                model="local",
                messages=full_messages,
                temperature=temperature,
                max_tokens=max_tokens,
            ),
        )
        text = response.choices[0].message.content or ""
        try:
            tokens = response.usage.total_tokens
        except Exception:
            tokens = self._estimate_tokens(messages, text, system)
        return text, tokens

    # ------------------------------------------------------------------
    # Fallback chain con exponential backoff
    # Retorna (text, tokens, provider_usado) para Bug C fix
    # ------------------------------------------------------------------

    async def _fallback_chain(
        self, messages, system, temperature, max_tokens, failed: str
    ) -> Tuple[str, int, str]:
        """
        Intenta providers en orden de prioridad con exponential backoff.
        Retorna (text, tokens, provider_real) para trazabilidad de costos.
        """
        priority  = ["ollama", "groq", "gemini", "hyperspace"]
        available = {
            "ollama":     self.ollama_enabled,
            "groq":       bool(self.groq_key),
            "gemini":     bool(self.gemini_key),
            "hyperspace": self.hyperspace_enabled,
        }

        attempt = 0
        for provider in priority:
            if provider == failed or not available[provider]:
                continue

            if attempt > 0:
                wait = 2 ** (attempt - 1)  # 1s, 2s, 4s
                logger.info(f"APIRouter fallback: esperando {wait}s antes de {provider}")
                await asyncio.sleep(wait)

            try:
                logger.info(f"APIRouter fallback [{attempt+1}] → {provider}")
                text, tokens = await self._call(provider, messages, system, temperature, max_tokens)
                return text, tokens, provider  # provider REAL
            except Exception as e:
                logger.warning(f"Fallback {provider} también falló: {e}")
                attempt += 1

        raise RuntimeError(
            "Todos los providers fallaron.\n"
            "Verifica: OLLAMA_ENABLED, GROQ_API_KEY, GEMINI_API_KEY en .env"
        )

    # ------------------------------------------------------------------
    # Utilidades
    # ------------------------------------------------------------------

    @staticmethod
    def _estimate_tokens(
        messages: list,
        response_text: str,
        system: Optional[str] = None,
        task_type: str = "coding",
    ) -> int:
        CODE_TASKS = {"coding", "qa", "dev", "review", "security_audit"}
        factor   = 1.6 if task_type in CODE_TASKS else 1.3
        all_text = " ".join(m.get("content", "") for m in messages)
        if system:
            all_text += " " + system
        all_text += " " + (response_text or "")
        return max(1, int(len(all_text.split()) * factor))

    def cost_for_tokens(self, tokens: int, provider: str) -> float:
        rate = COST_PER_1K.get(provider, 0.0)
        return round((tokens / 1000) * rate, 6)

    def status(self) -> dict:
        return {
            "strategy":             self._strategy,
            "hw_profile":           self.hw_profile,
            "ollama_enabled":       self.ollama_enabled,
            "ollama_model":         self.ollama_model if self.ollama_enabled else None,
            "ollama_url":           self.ollama_url   if self.ollama_enabled else None,
            "gpu_layers":           self.ollama_layers,
            "context_size":         self.ollama_context,
            "groq_available":       bool(self.groq_key),
            "gemini_available":     bool(self.gemini_key),
            "hyperspace_available": self.hyperspace_enabled,
            "cloud_context_limits": CLOUD_CONTEXT_LIMITS,
            "providers_priority":   ["ollama", "groq", "gemini", "hyperspace"],
        }
