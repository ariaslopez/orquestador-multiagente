"""Punto de entrada del Orquestador Multi-Agente."""
import logging
import argparse
from core.orchestrator import Orchestrator
from core.pipeline import Pipeline
from agents import LanguageAgent, SearchAgent, DocAgent, CodeAgent, ResponseAgent

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)


def build_default_pipeline(use_llm: bool = False) -> Pipeline:
    """Construye el pipeline estándar de documentación."""
    return (
        Pipeline(name="docs_pipeline", description="Pipeline para consultas de documentación")
        .add_agent(LanguageAgent())
        .add_agent(SearchAgent())
        .add_agent(DocAgent())
        .add_agent(CodeAgent())
        .add_agent(ResponseAgent(use_llm=use_llm))
    )


def main():
    parser = argparse.ArgumentParser(description="Orquestador Multi-Agente Local")
    parser.add_argument("query", nargs="?", help="Consulta a procesar")
    parser.add_argument("--llm", action="store_true", help="Usar LLM local (Ollama)")
    parser.add_argument("--files", nargs="*", default=[], help="Archivos de código a analizar")
    parser.add_argument("--interactive", "-i", action="store_true", help="Modo interactivo")
    args = parser.parse_args()

    orchestrator = Orchestrator()
    pipeline = build_default_pipeline(use_llm=args.llm)
    orchestrator.register_pipeline(pipeline, default=True)

    if args.interactive:
        print("🤖 Orquestador Multi-Agente — Modo Interactivo (offline)")
        print("   Escribe tu consulta o 'salir' para terminar\n")
        while True:
            query = input("📝 Consulta: ").strip()
            if query.lower() in ("salir", "exit", "quit"):
                break
            if not query:
                continue
            context = orchestrator.run(query)
            print("\n" + "=" * 60)
            print(context.final_response)
            print("=" * 60 + "\n")
    elif args.query:
        context = orchestrator.run(args.query, user_files=args.files)
        print(context.final_response)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
