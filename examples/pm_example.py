"""Ejemplo: plan de proyecto con el pipeline PM."""
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
            "Crea un plan de proyecto completo para un SaaS multi-tenant de bots de trading "
            "en X (Twitter), con panel, billing y orquestador multi-agente."
        ),
        task_type='pm',
        auto_mode=True,
    )
    print(ctx.final_output)


if __name__ == '__main__':
    asyncio.run(main())
