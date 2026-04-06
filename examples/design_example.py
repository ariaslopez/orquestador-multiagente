"""Ejemplo de uso del DESIGN pipeline."""
import asyncio
from core.maestro import Maestro


async def main():
    maestro = Maestro()
    result = await maestro.run(
        user_input="Diseña el sistema visual completo para un dashboard SaaS de analytics en modo oscuro",
        task_type="design",
    )
    print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())
