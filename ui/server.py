"""Dashboard web del CLAW Agent System via FastAPI."""
from __future__ import annotations
import asyncio
import os
from pathlib import Path
from typing import Optional


def start_server(host: str = '127.0.0.1', port: int = 8000) -> None:
    try:
        import uvicorn
        from fastapi import FastAPI, HTTPException
        from fastapi.responses import HTMLResponse, JSONResponse
        from pydantic import BaseModel
    except ImportError:
        print("Falta fastapi/uvicorn: pip install fastapi uvicorn")
        return

    app = FastAPI(title="CLAW Agent System", version="2.0.0")

    class TaskRequest(BaseModel):
        task: str
        task_type: Optional[str] = None
        input_file: Optional[str] = None
        auto: bool = True

    @app.get('/', response_class=HTMLResponse)
    async def index():
        html_path = Path(__file__).parent / 'index.html'
        if html_path.exists():
            return html_path.read_text(encoding='utf-8')
        return HTMLResponse(content=FALLBACK_HTML)

    @app.get('/api/health')
    async def health():
        return {'status': 'ok', 'version': '2.0.0'}

    @app.post('/api/task')
    async def run_task(req: TaskRequest):
        from infrastructure.input_sanitizer import InputSanitizer
        from infrastructure.memory_manager import MemoryManager
        from core.maestro import Maestro

        # FIX 1: assert_safe es sincrono — correr en executor para no bloquear el event loop
        loop = asyncio.get_running_loop()
        sanitizer = InputSanitizer()
        try:
            clean_task = await loop.run_in_executor(None, sanitizer.assert_safe, req.task)
        except ValueError as e:
            # FIX 2: usar HTTPException en lugar de retornar tupla (FastAPI no soporta tuplas)
            raise HTTPException(status_code=400, detail=str(e))

        memory = MemoryManager()
        maestro = Maestro(memory_manager=memory)

        try:
            ctx = await maestro.run(
                user_input=clean_task,
                task_type=req.task_type,
                input_file=req.input_file,
                auto_mode=req.auto,
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error interno del pipeline: {e}")

        return JSONResponse(content={
            'session_id': ctx.session_id,
            'pipeline': ctx.pipeline_name,
            'output': ctx.final_output,
            'tokens': ctx.total_tokens,
            'cost_usd': ctx.estimated_cost_usd,
            'duration': ctx.duration_seconds,
            'status': ctx.status,
            'error': ctx.error,
        })

    @app.get('/api/sessions')
    async def get_sessions():
        from infrastructure.memory_manager import MemoryManager
        return MemoryManager().get_all_sessions(limit=20)

    @app.get('/api/stats')
    async def get_stats():
        from infrastructure.memory_manager import MemoryManager
        return MemoryManager().get_usage_stats()

    @app.get('/api/metrics')
    async def get_metrics():
        from infrastructure.audit_logger import AuditLogger
        audit = AuditLogger()
        stats = audit.get_pipeline_stats()
        most_used = audit.get_most_used_pipeline()
        total_tokens = sum(v['total_tokens'] for v in stats.values())
        total_cost = sum(v['total_cost_usd'] for v in stats.values())
        total_calls = sum(v['calls'] for v in stats.values())
        return {
            'pipelines': stats,
            'most_used_pipeline': most_used,
            'totals': {
                'calls': total_calls,
                'tokens': total_tokens,
                'cost_usd': round(total_cost, 6),
                'avg_tokens_per_call': round(total_tokens / max(total_calls, 1), 1),
            },
        }

    print(f"\n🧠 CLAW Dashboard corriendo en http://{host}:{port}")
    uvicorn.run(app, host=host, port=port, log_level='warning')


FALLBACK_HTML = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CLAW Agent System</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-900 text-white min-h-screen p-6">
    <div class="max-w-5xl mx-auto">
        <h1 class="text-3xl font-bold text-cyan-400 mb-1">CLAW Agent System</h1>
        <p class="text-gray-400 text-sm mb-6">Orquestador autonomo multi-agente v2.0 &mdash; 12 pipelines</p>
        <div class="bg-gray-800 rounded-lg p-4 mb-4">
            <textarea id="task" class="w-full bg-gray-700 text-white rounded p-3 mb-3 h-24 resize-none"
                placeholder="Describe tu tarea..."></textarea>
            <div class="flex gap-2">
                <select id="pipeline" class="bg-gray-700 text-white rounded px-3 py-2 text-sm">
                    <option value="">Auto-detectar</option>
                    <option value="dev">DEV</option>
                    <option value="research">RESEARCH</option>
                    <option value="content">CONTENT</option>
                    <option value="office">OFFICE</option>
                    <option value="qa">QA</option>
                    <option value="trading">TRADING</option>
                    <option value="pm">PM</option>
                    <option value="analytics">ANALYTICS</option>
                    <option value="marketing">MARKETING</option>
                    <option value="product">PRODUCT</option>
                    <option value="security_audit">SECURITY AUDIT</option>
                    <option value="design">DESIGN</option>
                </select>
                <button id="btn" onclick="runTask()" class="bg-cyan-600 hover:bg-cyan-500 px-6 py-2 rounded font-medium">
                    Ejecutar
                </button>
            </div>
        </div>
        <div id="output" class="bg-gray-800 rounded-lg p-4 hidden">
            <div class="flex items-center gap-2 mb-3">
                <span id="status-dot" class="w-3 h-3 rounded-full bg-yellow-400"></span>
                <span id="status-text" class="text-sm text-gray-400">Procesando...</span>
                <span id="pipeline-badge" class="ml-auto bg-cyan-900 text-cyan-300 px-2 py-0.5 rounded text-xs"></span>
            </div>
            <pre id="result" class="text-sm text-gray-200 whitespace-pre-wrap"></pre>
        </div>
    </div>
    <script>
    async function runTask() {
        const task = document.getElementById('task').value.trim();
        const pipeline = document.getElementById('pipeline').value;
        if (!task) return alert('Escribe una tarea primero');

        const btn = document.getElementById('btn');
        btn.disabled = true;
        btn.textContent = 'Ejecutando...';

        const out = document.getElementById('output');
        out.classList.remove('hidden');
        document.getElementById('status-dot').className = 'w-3 h-3 rounded-full bg-yellow-400 animate-pulse';
        document.getElementById('status-text').textContent = 'Procesando (puede tardar 10-60s)...';
        document.getElementById('result').textContent = '';

        try {
            const controller = new AbortController();
            const timeout = setTimeout(() => controller.abort(), 300000); // 5 min
            const resp = await fetch('/api/task', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({task, task_type: pipeline || null, auto: true}),
                signal: controller.signal,
            });
            clearTimeout(timeout);

            if (!resp.ok) {
                const err = await resp.json().catch(() => ({detail: resp.statusText}));
                throw new Error(err.detail || resp.statusText);
            }

            const data = await resp.json();
            document.getElementById('status-dot').className = 'w-3 h-3 rounded-full bg-green-400';
            document.getElementById('status-text').textContent =
                `Completado en ${(data.duration??0).toFixed(1)}s | ${(data.tokens??0).toLocaleString()} tokens | $${(data.cost_usd??0).toFixed(4)} USD`;
            document.getElementById('pipeline-badge').textContent = data.pipeline || pipeline || 'AUTO';
            document.getElementById('result').textContent = data.output || '(sin output)';
        } catch(e) {
            document.getElementById('status-dot').className = 'w-3 h-3 rounded-full bg-red-400';
            document.getElementById('status-text').textContent = 'Error: ' + e.message;
        } finally {
            btn.disabled = false;
            btn.textContent = 'Ejecutar';
        }
    }
    </script>
</body>
</html>
"""
