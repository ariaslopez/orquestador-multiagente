"""Ejemplo de uso del ANALYTICS pipeline."""
import asyncio
from core.maestro import Maestro


async def main():
    maestro = Maestro()
    result = await maestro.run(
        user_input="Analiza el rendimiento de ventas del último trimestre y genera insights accionables",
        task_type="analytics",
    )
    print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())
