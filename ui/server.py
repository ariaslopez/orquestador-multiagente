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

    @app.post('/api/task')
    async def run_task(req: TaskRequest):
        from infrastructure.input_sanitizer import InputSanitizer
        from infrastructure.memory_manager import MemoryManager
        from core.maestro import Maestro

        try:
            clean_task = InputSanitizer().assert_safe(req.task)
        except ValueError as e:
            return {'error': str(e), 'status': 'rejected'}, 400

        memory = MemoryManager()
        maestro = Maestro(memory_manager=memory)
        ctx = await maestro.run(
            user_input=clean_task,
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

    @app.get('/api/metrics')
    async def get_metrics():
        """Metricas de observabilidad: tokens/sesion, pipeline mas usado, costos."""
        from infrastructure.audit_logger import AuditLogger
        from infrastructure.memory_manager import MemoryManager

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

    @app.websocket('/ws/task')
    async def ws_task(websocket: WebSocket):
        await websocket.accept()
        try:
            data = await websocket.receive_json()
            task = data.get('task', '')
            if not task:
                await websocket.send_json({'error': 'task requerido'})
                return

            from infrastructure.input_sanitizer import InputSanitizer
            try:
                task = InputSanitizer().assert_safe(task)
            except ValueError as e:
                await websocket.send_json({'status': 'rejected', 'message': str(e)})
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
                'tokens': getattr(ctx, 'total_tokens', 0),
                'cost_usd': getattr(ctx, 'estimated_cost_usd', 0.0),
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
    <div class="max-w-5xl mx-auto">
        <div class="flex items-center justify-between mb-6">
            <div>
                <h1 class="text-3xl font-bold text-cyan-400">CLAW Agent System</h1>
                <p class="text-gray-400 text-sm">Orquestador autonomo multi-agente v2.0 &mdash; 12 pipelines</p>
            </div>
            <button onclick="loadMetrics()" class="bg-gray-700 hover:bg-gray-600 px-4 py-2 rounded text-sm">
                Ver metricas
            </button>
        </div>

        <!-- Metricas panel -->
        <div id="metrics-panel" class="hidden bg-gray-800 rounded-lg p-4 mb-4">
            <h2 class="text-lg font-semibold text-cyan-300 mb-3">Observabilidad</h2>
            <div id="metrics-content" class="text-sm text-gray-300"></div>
        </div>

        <div class="bg-gray-800 rounded-lg p-4 mb-4">
            <textarea id="task" class="w-full bg-gray-700 text-white rounded p-3 mb-3 h-24 resize-none"
                placeholder="Describe tu tarea en lenguaje natural..."></textarea>
            <div class="flex gap-2">
                <select id="pipeline" class="bg-gray-700 text-white rounded px-3 py-2 text-sm">
                    <option value="">Auto-detectar pipeline</option>
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
            if (data.status === 'rejected') {
                document.getElementById('status-dot').className = 'w-3 h-3 rounded-full bg-red-400';
                document.getElementById('status-text').textContent = 'Rechazado: ' + data.error;
                return;
            }
            document.getElementById('status-dot').className = 'w-3 h-3 rounded-full bg-green-400';
            document.getElementById('status-text').textContent = `${data.duration?.toFixed(1)}s | ${data.tokens?.toLocaleString()} tokens | $${data.cost_usd?.toFixed(4)}`;
            document.getElementById('pipeline-badge').textContent = data.pipeline || '';
            document.getElementById('result').textContent = data.output || '(sin output)';
        } catch(e) {
            document.getElementById('status-dot').className = 'w-3 h-3 rounded-full bg-red-400';
            document.getElementById('status-text').textContent = 'Error: ' + e.message;
        }
    }

    async function loadMetrics() {
        const panel = document.getElementById('metrics-panel');
        panel.classList.toggle('hidden');
        if (panel.classList.contains('hidden')) return;

        try {
            const resp = await fetch('/api/metrics');
            const data = await resp.json();
            const totals = data.totals || {};
            const pipelines = data.pipelines || {};

            let html = `<div class="grid grid-cols-4 gap-3 mb-4">
                <div class="bg-gray-700 rounded p-3 text-center">
                    <div class="text-2xl font-bold text-cyan-400">${totals.calls ?? 0}</div>
                    <div class="text-xs text-gray-400">Total llamadas</div>
                </div>
                <div class="bg-gray-700 rounded p-3 text-center">
                    <div class="text-2xl font-bold text-green-400">${(totals.tokens ?? 0).toLocaleString()}</div>
                    <div class="text-xs text-gray-400">Tokens totales</div>
                </div>
                <div class="bg-gray-700 rounded p-3 text-center">
                    <div class="text-2xl font-bold text-yellow-400">$${(totals.cost_usd ?? 0).toFixed(4)}</div>
                    <div class="text-xs text-gray-400">Costo total USD</div>
                </div>
                <div class="bg-gray-700 rounded p-3 text-center">
                    <div class="text-2xl font-bold text-purple-400">${data.most_used_pipeline ?? '-'}</div>
                    <div class="text-xs text-gray-400">Pipeline mas usado</div>
                </div>
            </div>`;

            if (Object.keys(pipelines).length > 0) {
                html += '<table class="w-full text-xs"><thead><tr class="text-gray-400 border-b border-gray-600">';
                html += '<th class="text-left py-1">Pipeline</th><th>Llamadas</th><th>Tokens</th><th>Costo</th><th>Avg ms</th><th>Error %</th>';
                html += '</tr></thead><tbody>';
                for (const [pipe, s] of Object.entries(pipelines)) {
                    html += `<tr class="border-b border-gray-700">
                        <td class="py-1 text-cyan-300">${pipe}</td>
                        <td class="text-center">${s.calls}</td>
                        <td class="text-center">${s.total_tokens.toLocaleString()}</td>
                        <td class="text-center">$${s.total_cost_usd.toFixed(4)}</td>
                        <td class="text-center">${s.avg_duration_ms}</td>
                        <td class="text-center">${(s.error_rate * 100).toFixed(1)}%</td>
                    </tr>`;
                }
                html += '</tbody></table>';
            } else {
                html += '<p class="text-gray-500 text-xs">Sin trazas registradas aun. Ejecuta algunas tareas primero.</p>';
            }

            document.getElementById('metrics-content').innerHTML = html;
        } catch(e) {
            document.getElementById('metrics-content').textContent = 'Error cargando metricas: ' + e.message;
        }
    }
    </script>
</body>
</html>
"""
