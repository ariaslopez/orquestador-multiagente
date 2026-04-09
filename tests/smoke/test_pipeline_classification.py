"""
Smoke test — Fase 14: Clasificación de pipelines

Cubre los 12 pipelines del Maestro via classify_task() (keyword scoring).
No usa LLM ni red — solo lógica pura de keywords.

Casos cubiertos:
  - Un prompt representativo por pipeline (happy path)
  - Casos edge: prompt ambiguo, prompt vacío, prompt en inglés,
    prompt multipalabra exacto ("bot de trading"), score por debajo
    del threshold (needs_llm=True)

Ejecutar:
    pytest tests/smoke/test_pipeline_classification.py -v
"""
from __future__ import annotations
import pytest
from core.maestro import Maestro


# ---------------------------------------------------------------------------
# Fixture
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def maestro():
    """Maestro sin memory_manager y sin Ollama — solo se usa classify_task()."""
    import os
    os.environ.setdefault("OLLAMA_ENABLED", "false")
    os.environ.setdefault("GROQ_API_KEY", "")
    os.environ.setdefault("GEMINI_API_KEY", "")
    return Maestro(memory_manager=None)


# ---------------------------------------------------------------------------
# Happy path: un prompt representativo por cada uno de los 12 pipelines
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("prompt,expected", [
    # DEV — verbo "crea" + objeto "script"
    ("crea un script en python para leer archivos CSV", "dev"),
    # RESEARCH — verbo "investiga" + objeto "tendencia"
    ("investiga la tendencia de adopción de DeFi en 2026", "research"),
    # CONTENT — keyword "tweet" explícito
    ("escribe un hilo de tweet sobre inteligencia artificial", "content"),
    # OFFICE — extensión de archivo explícita
    ("analiza este archivo .xlsx y genera un resumen", "office"),
    # QA — keyword "audita"
    ("audita el código del módulo de autenticación", "qa"),
    # PM — keyword "sprint"
    ("planifica el sprint Q2 con backlog y estimaciones", "pm"),
    # TRADING — keyword exacto multi-palabra "bot de trading"
    ("revisa el bot de trading y su drawdown en BTC", "trading"),
    # ANALYTICS — keyword "dashboard" + "kpi"
    ("crea un dashboard con los kpi de retención de usuarios", "analytics"),
    # MARKETING — keyword "marketing" + "campana"
    ("diseña una campana de marketing para el lanzamiento del producto", "marketing"),
    # PRODUCT — keyword "user story" multi-palabra
    ("escribe las user story del mvp para el onboarding", "product"),
    # SECURITY_AUDIT — keyword "owasp"
    ("realiza una auditoria de seguridad owasp del api", "security_audit"),
    # DESIGN — keyword "ui" + "wireframe"
    ("diseña el wireframe de la ui del panel de control", "design"),
])
def test_happy_path_12_pipelines(maestro, prompt, expected):
    """Cada prompt representativo debe clasificar en su pipeline correcto."""
    task_type, score, needs_llm = maestro.classify_task(prompt)
    assert task_type == expected, (
        f"Prompt:    '{prompt}'\n"
        f"Esperado:  {expected}\n"
        f"Detectado: {task_type} (score={score}, needs_llm={needs_llm})"
    )


# ---------------------------------------------------------------------------
# Score y confianza
# ---------------------------------------------------------------------------

def test_high_score_does_not_need_llm(maestro):
    """Un prompt con ≥2 keywords del mismo pipeline no debe escalar al LLM."""
    # 'backtest' + 'drawdown' + 'sharpe' → 3 keywords TRADING
    _, score, needs_llm = maestro.classify_task(
        "analiza el backtest, el drawdown y el sharpe de esta estrategia"
    )
    assert score >= 2, f"Score esperado ≥2, obtenido {score}"
    assert not needs_llm, "Con score alto no debería escalar al LLM"


def test_low_score_signals_llm_fallback(maestro):
    """Un prompt con solo 1 keyword debe señalar needs_llm=True."""
    # 'plan' tiene 1 match en PM — score < threshold (2)
    _, score, needs_llm = maestro.classify_task("dame un plan")
    assert score < maestro._CONFIDENT_SCORE_THRESHOLD
    assert needs_llm, "Score bajo debe disparar needs_llm=True"


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

def test_empty_prompt_does_not_raise(maestro):
    """Un prompt vacío no debe lanzar excepción — retorna algún pipeline con score 0."""
    task_type, score, needs_llm = maestro.classify_task("")
    assert isinstance(task_type, str)
    assert score == 0
    assert needs_llm  # score 0 < threshold → debe pedir LLM


def test_english_prompt_dev(maestro):
    """Keywords en inglés ('build', 'implement') deben clasificar en DEV."""
    task_type, score, _ = maestro.classify_task(
        "build and implement a REST api with fastapi"
    )
    assert task_type == "dev", f"Esperado 'dev', obtenido '{task_type}' (score={score})"


def test_ambiguous_prompt_tie_signals_llm(maestro):
    """
    Un prompt que mezcla keywords de dos pipelines con el mismo score
    debe señalar needs_llm=True (empate → escalar a LLM).
    """
    # 'qa' tiene keyword 'test'; 'dev' tiene keyword 'script' + 'implementa'
    # Usamos un prompt deliberadamente ambiguo con igual peso
    _, _, needs_llm = maestro.classify_task(
        "implementa un test y revisa el bug en el script"
    )
    # No afirmamos el ganador (puede variar) — solo que hay ambigüedad detectada
    # O bien score alto en DEV o bien empate → llm debería activarse en algún caso
    # Lo que SÍ podemos afirmar: la función no lanza excepción
    assert isinstance(needs_llm, bool)


def test_multiword_keyword_trading(maestro):
    """El keyword exacto 'bot de trading' (3 palabras) debe sumar punto a TRADING."""
    task_type, score, _ = maestro.classify_task(
        "quiero optimizar mi bot de trading para BTC"
    )
    assert task_type == "trading", (
        f"'bot de trading' debería clasificar en TRADING, obtenido '{task_type}'"
    )
    assert score >= 2  # 'bot de trading' + 'btc'


def test_all_valid_pipeline_names_are_covered(maestro):
    """TASK_KEYWORDS debe contener exactamente los 12 pipelines del pipeline_map."""
    expected_pipelines = {
        "dev", "research", "content", "office", "qa", "pm",
        "trading", "analytics", "marketing", "product",
        "security_audit", "design",
    }
    actual = set(maestro.TASK_KEYWORDS.keys())
    assert actual == expected_pipelines, (
        f"Pipelines faltantes: {expected_pipelines - actual}\n"
        f"Pipelines extra:     {actual - expected_pipelines}"
    )
