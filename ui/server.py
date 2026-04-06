"""Dashboard web del CLAW Agent System via FastAPI."""
from __future__ import annotations
import asyncio
import json
import os
from pathlib import Path
from typing import Optional


def start_server(host: str = '127.0.0.1', port: int = 8000) -> None:
    try:
        import uvicorn
        from fastapi import FastAPI, WebSocket, WebSocketDisconnect
        from fastapi.staticfiles import StaticFiles
        from fastapi.responses import HTMLResponse
        from pydantic import BaseModel
    except ImportError:
        print("Falta fastapi/uvicorn: pip install fastapi uvicorn")
        return

    app = FastAPI(title="CLAW Agent System", version="1.0.0")

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

    @app.post('/api/task')
    async def run_task(req: TaskRequest):
        from infrastructure.memory_manager import MemoryManager
        from core.maestro import Maestro
        memory = MemoryManager()
        maestro = Maestro(memory_manager=memory)
        ctx = await maestro.run(
            user_input=req.task,
            task_type=req.task_type,
            input_file=req.input_file,
            auto_mode=req.auto,
        )
        return {
            'session_id': ctx.session_id,
            'pipeline': ctx.pipeline_name,
            'output': ctx.final_output,
            'tokens': getattr(ctx, 'total_tokens', 0),
            'cost_usd': getattr(ctx, 'estimated_cost_usd', 0.0),
            'duration': getattr(ctx, 'duration_seconds', 0.0),
        }

    @app.get('/api/sessions')
    async def get_sessions():
        from infrastructure.memory_manager import MemoryManager
        return MemoryManager().get_all_sessions(limit=20)

    @app.get('/api/stats')
    async def get_stats():
        from infrastructure.memory_manager import MemoryManager
        return MemoryManager().get_usage_stats()

    @app.websocket('/ws/task')
    async def ws_task(websocket: WebSocket):
        await websocket.accept()
        try:
            data = await websocket.receive_json()
            task = data.get('task', '')
            if not task:
                await websocket.send_json({'error': 'task requerido'})
                return
            await websocket.send_json({'status': 'running', 'message': 'Iniciando pipeline...'})
            from infrastructure.memory_manager import MemoryManager
            from core.maestro import Maestro
            memory = MemoryManager()
            maestro = Maestro(memory_manager=memory)
            ctx = await maestro.run(user_input=task, auto_mode=True)
            await websocket.send_json({
                'status': 'completed',
                'pipeline': ctx.pipeline_name,
                'output': ctx.final_output,
                'session_id': ctx.session_id,
            })
        except WebSocketDisconnect:
            pass
        except Exception as e:
            await websocket.send_json({'status': 'error', 'message': str(e)})

    print(f"\n CLAW Dashboard corriendo en http://{host}:{port}")
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
    <div class="max-w-4xl mx-auto">
        <h1 class="text-3xl font-bold text-cyan-400 mb-2">CLAW Agent System</h1>
        <p class="text-gray-400 mb-6">Orquestador autonomo multi-agente v1.0</p>

        <div class="bg-gray-800 rounded-lg p-4 mb-4">
            <textarea id="task" class="w-full bg-gray-700 text-white rounded p-3 mb-3 h-24 resize-none"
                placeholder="Describe tu tarea en lenguaje natural..."></textarea>
            <div class="flex gap-2">
                <select id="pipeline" class="bg-gray-700 text-white rounded px-3 py-2">
                    <option value="">Auto-detectar pipeline</option>
                    <option value="dev">DEV - Generar proyecto</option>
                    <option value="research">RESEARCH - Tesis de inversion</option>
                    <option value="content">CONTENT - Generar contenido</option>
                    <option value="office">OFFICE - Analizar archivo</option>
                    <option value="qa">QA - Auditar codigo</option>
                    <option value="trading">TRADING - Analytics</option>
                    <option value="pm">PM - Plan de proyecto</option>
                </select>
                <button onclick="runTask()" class="bg-cyan-600 hover:bg-cyan-500 px-6 py-2 rounded font-medium">
                    Ejecutar
                </button>
            </div>
        </div>

        <div id="output" class="bg-gray-800 rounded-lg p-4 min-h-32 hidden">
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

        const out = document.getElementById('output');
        out.classList.remove('hidden');
        document.getElementById('status-dot').className = 'w-3 h-3 rounded-full bg-yellow-400 animate-pulse';
        document.getElementById('status-text').textContent = 'Procesando...';
        document.getElementById('result').textContent = '';

        try {
            const resp = await fetch('/api/task', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({task, task_type: pipeline || null, auto: true})
            });
            const data = await resp.json();
            document.getElementById('status-dot').className = 'w-3 h-3 rounded-full bg-green-400';
            document.getElementById('status-text').textContent = `Completado en ${data.duration?.toFixed(1)}s | ${data.tokens?.toLocaleString()} tokens | $${data.cost_usd?.toFixed(4)} USD`;
            document.getElementById('pipeline-badge').textContent = data.pipeline || '';
            document.getElementById('result').textContent = data.output || '(sin output)';
        } catch(e) {
            document.getElementById('status-dot').className = 'w-3 h-3 rounded-full bg-red-400';
            document.getElementById('status-text').textContent = 'Error: ' + e.message;
        }
    }
    </script>
</body>
</html>
"""
