"""Ejemplo: generar un proyecto completo con el pipeline DEV."""
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
            "Crea una API REST en FastAPI para gestionar senales de trading crypto. "
            "Debe tener: autenticacion JWT, endpoints CRUD para senales, "
            "conexion a Supabase, documentacion Swagger automatica y tests basicos."
        ),
        task_type='dev',
        auto_mode=True,
    )
    print(f"\n Pipeline: {ctx.pipeline_name}")
    print(f" Output en: {ctx.output_path}")
    print(f" Tokens: {getattr(ctx, 'total_tokens', 0):,}")
    print(f" Costo: ${getattr(ctx, 'estimated_cost_usd', 0):.4f} USD")
    print(f"\n{ctx.final_output}")


if __name__ == '__main__':
    asyncio.run(main())
