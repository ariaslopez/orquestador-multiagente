"""Ejemplo de uso del PRODUCT pipeline."""
import asyncio
from core.maestro import Maestro


async def main():
    maestro = Maestro()
    result = await maestro.run(
        user_input="Define la visión y roadmap de producto para una app de finanzas personales para millennials",
        task_type="product",
    )
    print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())
