"""Ejemplo: generar contenido cripto con el pipeline CONTENT."""
import asyncio
import sys
sys.path.insert(0, '.')

from dotenv import load_dotenv
load_dotenv()

from infrastructure.memory_manager import MemoryManager
from core.maestro import Maestro


async def main():
    memory = MemoryManager()
    maestro = Maestro(memory_manager=memory)

    ctx = await maestro.run(
        user_input=(
            "Hilo de 8 tweets sobre la dominancia de BTC en Q1 2026, "
            "tono analitico para traders profesionales."
        ),
        task_type='content',
        auto_mode=True,
    )
    print(ctx.final_output)


if __name__ == '__main__':
    asyncio.run(main())
