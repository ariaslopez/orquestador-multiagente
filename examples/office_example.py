"""Ejemplo: analizar archivo Office/PDF con el pipeline OFFICE.

Para probarlo, apunta `input_file` a un .xlsx/.csv/.pdf existente.
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
            "Analiza este archivo de backtesting y dame un resumen ejecutivo "
            "con las metricas mas importantes y que parametros mejorar."
        ),
        task_type='office',
        input_file='data/backtest_sample.xlsx',  # ajusta la ruta a tu archivo
        auto_mode=True,
    )
    print(ctx.final_output)


if __name__ == '__main__':
    asyncio.run(main())
