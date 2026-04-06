"""Ejemplo: tesis de inversion con el pipeline RESEARCH."""
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
            "Tesis completa sobre el ecosistema Layer 2 de Ethereum: "
            "Arbitrum, Optimism y Base. Analisis de adopcion, TVL, "
            "metricas de red y perspectivas para Q2 2026."
        ),
        task_type='research',
        auto_mode=True,
    )
    print(ctx.final_output)


if __name__ == '__main__':
    asyncio.run(main())
