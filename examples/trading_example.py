"""Ejemplo: analytics de trading con el pipeline TRADING.

Apunta `input_file` a un CSV de operaciones o logs de tu bot.
"""
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
            "Analiza el performance del bot de trading V4-Pro y sugiere ajustes de parametros."
        ),
        task_type='trading',
        input_file='data/trades_sample.csv',  # ajusta la ruta a tu CSV
        auto_mode=True,
    )
    print(ctx.final_output)


if __name__ == '__main__':
    asyncio.run(main())
