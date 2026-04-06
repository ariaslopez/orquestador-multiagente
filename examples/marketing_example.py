"""Ejemplo de uso del MARKETING pipeline."""
import asyncio
from core.maestro import Maestro


async def main():
    maestro = Maestro()
    result = await maestro.run(
        user_input="Crea el plan de marketing completo para un SaaS de gestión de inventarios B2B",
        task_type="marketing",
    )
    print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())
