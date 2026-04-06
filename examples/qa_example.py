"""Ejemplo: auditoria de codigo con el pipeline QA."""
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
            "Audita este modulo de Python buscando bugs criticos, vulnerabilidades y gaps de tests."
        ),
        task_type='qa',
        input_file='examples/dev_example.py',  # archivo de ejemplo a auditar
        auto_mode=True,
    )
    print(ctx.final_output)


if __name__ == '__main__':
    asyncio.run(main())
