"""Dashboard web del CLAW Agent System via FastAPI."""
from __future__ import annotations
import asyncio
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

try:
    from pydantic import BaseModel, field_validator
    from fastapi import FastAPI, HTTPException, Header
    from fastapi.responses import HTMLResponse
    import uvicorn
    _DEPS_OK = True
except ImportError:
    _DEPS_OK = False
    BaseModel = object  # fallback para que el modulo cargue sin crash


if _DEPS_OK:
    class TaskRequest(BaseModel):
        task: str
        task_type: Optional[str] = None
        input_file: Optional[str] = None
        auto: bool = True

        @field_validator('task_type', 'input_file', mode='before')
        @classmethod
        def empty_str_to_none(cls, v):
            """Convierte string vacio a None — el select HTML envia '' sin seleccion."""
            if isinstance(v, str) and v.strip() == '':
                return None
            return v

    # ---------------------------------------------------------------------------
    # Modelos para la integración CLAW → Tweet Bot Platform
    # ---------------------------------------------------------------------------

    class OrchestratorTweetContent(BaseModel):
        text: str
        char_count: int
        language: str
        personality_used: str

    class OrchestratorScheduling(BaseModel):
        publish_at: Optional[str] = None  # ISO 8601 o null
        timezone: str = "America/Bogota"

    class OrchestratorMeta(BaseModel):
        pipeline_name: str
        trace_id: str
        tokens_used: int = 0
        model: str = "gpt-4.1-mini"

    class OrchestratorTweetPayload(BaseModel):
        """
        TwitterContentPayload generado por marketing-twitter-engager.
        Ref: agency-agents/integrations/twitter-bot-platform/INTEGRATION.md
        """
        status: str  # "ok" | "error"
        tweet: OrchestratorTweetContent
        alternatives: list[str] = []
        thread: list[str] = []
        scheduling: OrchestratorScheduling = OrchestratorScheduling()
        meta: OrchestratorMeta
        error: Optional[str] = None

    class OrchestratorTweetResponse(BaseModel):
        tweet_id: str
        status: str   # "queued" | "scheduled" | "published" | "error"
        publish_at: Optional[str] = None
        message: str


# ---------------------------------------------------------------------------
# Feature flag — activa la integración con CLAW cuando esté lista
# Poner CLAW_INTEGRATION_ENABLED=true en .env o en Fly.io secrets para habilitar.
# ---------------------------------------------------------------------------
_CLAW_INTEGRATION_ENABLED = os.getenv("CLAW_INTEGRATION_ENABLED", "false").lower() == "true"
_ORCHESTRATOR_SECRET = os.getenv("ORCHESTRATOR_SECRET", "")


def _verify_orchestrator_secret(authorization: str) -> None:
    """Valida el header Authorization: Bearer <ORCHESTRATOR_SECRET>."""
    if not _ORCHESTRATOR_SECRET:
        raise HTTPException(
            status_code=503,
            detail="ORCHESTRATOR_SECRET no configurado en el servidor.",
        )
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or token != _ORCHESTRATOR_SECRET:
        raise HTTPException(status_code=401, detail="Token de orquestador inválido.")


def start_server(host: str = '127.0.0.1', port: int = 8000) -> None:
    if not _DEPS_OK:
        print("Falta fastapi/uvicorn/pydantic: pip install fastapi uvicorn pydantic")
        return

    app = FastAPI(title="CLAW Agent System", version="2.4.0")

    @app.get('/', response_class=HTMLResponse)
    async def index():
        html_path = Path(__file__).parent / 'index.html'
        if html_path.exists():
            return html_path.read_text(encoding='utf-8')
        return HTMLResponse(content=FALLBACK_HTML)

    @app.get('/api/health')
    async def health():
        return {
            'status': 'ok',
            'version': '2.4.0',
            'claw_integration': _CLAW_INTEGRATION_ENABLED,
        }

    @app.post('/api/task')
    async def run_task(req: TaskRequest):
        from infrastructure.input_sanitizer import InputSanitizer
        from infrastructure.memory_manager import MemoryManager
        from core.maestro import Maestro

        loop = asyncio.get_event_loop()
        sanitizer = InputSanitizer()
        try:
            clean_task = await loop.run_in_executor(None, sanitizer.assert_safe, req.task)
        except ValueError as e:
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
            raise HTTPException(status_code=500, detail=f"Error interno: {e}")

        result = ctx.to_dict()
        result['output'] = ctx.final_output
        return result

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

    # ---------------------------------------------------------------------------
    # POST /api/orchestrator/tweet
    # Recibe el TwitterContentPayload del orquestador CLAW y lo encola
    # en la plataforma de bots para publicación inmediata o programada.
    #
    # INACTIVO hasta que CLAW_INTEGRATION_ENABLED=true en variables de entorno.
    # Ref: agency-agents/integrations/twitter-bot-platform/INTEGRATION.md
    # ---------------------------------------------------------------------------
    @app.post(
        '/api/orchestrator/tweet',
        response_model=OrchestratorTweetResponse,
        summary="[CLAW Integration] Recibe contenido generado por marketing-twitter-engager",
        tags=["orchestrator"],
        include_in_schema=_CLAW_INTEGRATION_ENABLED,  # oculto en /docs hasta activar
    )
    async def orchestrator_tweet(
        payload: OrchestratorTweetPayload,
        authorization: str = Header(..., description="Bearer <ORCHESTRATOR_SECRET>"),
        x_bot_id: Optional[str] = Header(None, alias="X-Bot-Id"),
    ):
        # ── Guard: feature flag ─────────────────────────────────────────────────
        if not _CLAW_INTEGRATION_ENABLED:
            raise HTTPException(
                status_code=503,
                detail=(
                    "Integración CLAW desactivada. "
                    "Configura CLAW_INTEGRATION_ENABLED=true cuando la integración esté lista."
                ),
            )

        # ── Guard: autenticación ────────────────────────────────────────────────
        _verify_orchestrator_secret(authorization)

        # ── Guard: payload inválido del agente ──────────────────────────────────
        if payload.status == "error":
            raise HTTPException(
                status_code=422,
                detail=f"El orquestador reportó error en el contenido: {payload.error}",
            )

        # ── Guard: longitud del tweet ───────────────────────────────────────────
        if len(payload.tweet.text) > 280:
            raise HTTPException(
                status_code=422,
                detail=(
                    f"El tweet supera 280 caracteres ({len(payload.tweet.text)}). "
                    "Solicita un rewrite al orquestador."
                ),
            )

        # ── Determinar status de publicación ────────────────────────────────────
        if payload.scheduling.publish_at:
            pub_status = "scheduled"
            publish_at = payload.scheduling.publish_at
        else:
            pub_status = "queued"
            publish_at = None

        tweet_id = str(uuid.uuid4())
        received_at = datetime.now(timezone.utc).isoformat()

        # ── Log de auditoría ─────────────────────────────────────────────────────
        # TODO (Fase CLAW): persistir en Supabase platform_tweets con los campos:
        #   tweet_id, bot_id (x_bot_id), text, personality_used, language,
        #   alternatives, thread_tweets, orchestrator_trace_id, pipeline_name,
        #   tokens_used, model_used, publish_at, status, received_at
        try:
            from infrastructure.audit_logger import AuditLogger
            AuditLogger().log(
                event="orchestrator_tweet_received",
                data={
                    "tweet_id": tweet_id,
                    "bot_id": x_bot_id,
                    "trace_id": payload.meta.trace_id,
                    "pipeline": payload.meta.pipeline_name,
                    "personality": payload.tweet.personality_used,
                    "char_count": payload.tweet.char_count,
                    "pub_status": pub_status,
                    "publish_at": publish_at,
                    "tokens_used": payload.meta.tokens_used,
                    "model": payload.meta.model,
                    "received_at": received_at,
                },
            )
        except Exception:
            # No bloquear la respuesta si el logger falla
            pass

        return OrchestratorTweetResponse(
            tweet_id=tweet_id,
            status=pub_status,
            publish_at=publish_at,
            message=(
                f"Tweet {'programado para ' + publish_at if publish_at else 'encolado para publicación automática'}. "
                f"trace_id={payload.meta.trace_id}"
            ),
        )

    print(f"\n🧠 CLAW Dashboard → http://{host}:{port}")
    if _CLAW_INTEGRATION_ENABLED:
        print(f"🔗 CLAW Integration ACTIVA → POST /api/orchestrator/tweet")
    else:
        print(f"⏸  CLAW Integration INACTIVA (CLAW_INTEGRATION_ENABLED=false)")
    uvicorn.run(app, host=host, port=port, log_level='info')


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
        <p class="text-gray-400 text-sm mb-6">Orquestador autonomo multi-agente v2.4 &mdash; 12 pipelines</p>
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
                <button id="btn" onclick="runTask()" class="bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 px-6 py-2 rounded font-medium">
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
        btn.disabled = true; btn.textContent = '⏳ Ejecutando...';
        const out = document.getElementById('output');
        out.classList.remove('hidden');
        document.getElementById('status-dot').className = 'w-3 h-3 rounded-full bg-yellow-400 animate-pulse';
        document.getElementById('status-text').textContent = 'Procesando (30-90s)...';
        document.getElementById('result').textContent = '';
        try {
            const ctrl = new AbortController();
            const tid = setTimeout(() => ctrl.abort(), 300000);
            const resp = await fetch('/api/task', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({task, task_type: pipeline || null, auto: true}),
                signal: ctrl.signal,
            });
            clearTimeout(tid);
            if (!resp.ok) {
                const err = await resp.json().catch(() => ({detail: resp.statusText}));
                throw new Error(err.detail || `HTTP ${resp.status}`);
            }
            const data = await resp.json();
            document.getElementById('status-dot').className = 'w-3 h-3 rounded-full bg-green-400';
            document.getElementById('status-text').textContent =
                `Completado en ${(data.duration_seconds??0).toFixed(1)}s | ${(data.total_tokens??0).toLocaleString()} tokens | $${(data.estimated_cost_usd??0).toFixed(4)} USD`;
            document.getElementById('pipeline-badge').textContent = data.pipeline_name || pipeline || 'AUTO';
            document.getElementById('result').textContent = data.output || data.final_output || '(sin output)';
        } catch(e) {
            document.getElementById('status-dot').className = 'w-3 h-3 rounded-full bg-red-400';
            document.getElementById('status-text').textContent = 'Error: ' + (e.name === 'AbortError' ? 'timeout >5min' : e.message);
        } finally {
            btn.disabled = false; btn.textContent = 'Ejecutar';
        }
    }
    </script>
</body>
</html>
"""
