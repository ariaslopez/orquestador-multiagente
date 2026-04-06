"""Ejemplo de uso del SECURITY_AUDIT pipeline."""
import asyncio
from core.maestro import Maestro


async def main():
    maestro = Maestro()
    result = await maestro.run(
        user_input="Audita la seguridad de una API REST Flask con autenticación JWT y conexión a PostgreSQL",
        task_type="security_audit",
    )
    print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())
