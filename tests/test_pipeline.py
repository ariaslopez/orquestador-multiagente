"""Tests básicos del pipeline multi-agente."""
import pytest
from core.orchestrator import Orchestrator
from core.pipeline import Pipeline
from core.context import AgentContext
from agents import LanguageAgent, ResponseAgent


def test_language_detection_python():
    agent = LanguageAgent()
    ctx = AgentContext(user_query="cómo usar decoradores en python")
    result = agent.run(ctx)
    assert result.detected_language == "python"


def test_language_detection_javascript():
    agent = LanguageAgent()
    ctx = AgentContext(user_query="how to use async await in javascript")
    result = agent.run(ctx)
    assert result.detected_language == "javascript"


def test_pipeline_runs_without_docs():
    orchestrator = Orchestrator()
    pipeline = (
        Pipeline(name="test")
        .add_agent(LanguageAgent())
        .add_agent(ResponseAgent(use_llm=False))
    )
    orchestrator.register_pipeline(pipeline, default=True)
    ctx = orchestrator.run("cómo hacer un loop en python")
    assert ctx.final_response is not None
    assert "LanguageAgent" in ctx.agents_executed


def test_context_error_handling():
    ctx = AgentContext(user_query="test")
    ctx.add_error("TestAgent", "Error de prueba")
    assert ctx.has_errors()
    assert "TestAgent" in ctx.errors
