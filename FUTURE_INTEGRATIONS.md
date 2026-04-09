# FUTURE_INTEGRATIONS — CLAW Agent System

> Última actualización: Abril 9, 2026
> Alcance: blueprint de integración de repositorios externos como servicios especializados dentro de CLAW.

---

## Visión de plataforma

CLAW no es un producto monolítico — es un **orquestador central** que coordina servicios especializados.
La estrategia de expansión es: cada dominio vertical se mantiene en su propio repositorio,
expone una API interna limpia, y CLAW lo consume a través de un MCP dedicado.

```
┌─────────────────────────────────────────────────────────────────┐
│                    CLAW Agent System (orquestador)               │
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────────┐  │
│  │  Pipeline    │  │  MCPHub      │  │  Dashboard UI           │  │
│  │  Router      │  │  (proxy      │  │  (panel unificado)      │  │
│  │              │  │  universal)  │  │                          │  │
│  └──────┬───────┘  └──────┬───────┘  └───────────┬────────────┘  │
│         │                 │                       │               │
└─────────┼─────────────────┼───────────────────────┼───────────────┘
          │                 │                       │
          ▼                 ▼                       ▼
  ┌───────────────┐  ┌─────────────────┐  ┌──────────────────────┐
  │ TweetBot      │  │ TradingBot      │  │ Futuros servicios    │
  │ Platform      │  │ v4-Pro          │  │ (crypto intel,       │
  │ (SaaS X/      │  │ (Motor RL       │  │  data hub, etc.)     │
  │  content)     │  │  PPO+LSTM)      │  │                      │
  └───────────────┘  └─────────────────┘  └──────────────────────┘
```

---

## Repositorios a integrar

### 1. `twitter-bot-platform` — TweetBot Platform

| Atributo | Detalle |
|---|---|
| Repositorio | https://github.com/ariaslopez/twitter-bot-platform |
| Estado actual | Fase 9/16 — Motor de publicación en construcción |
| Stack | Flask 3.1 + Supabase + OpenAI GPT-4.1 + Tweepy + Stripe |
| Función en CLAW | Servicio vertical de contenido para X (Twitter) |
| Pipeline CLAW objetivo | `content`, `marketing` |
| MCP a crear en CLAW | `x_tweetbot` |

**Capacidades disponibles para CLAW:**
- Crear y gestionar bots de X con personalidades IA definidas
- Generar lotes de tweets con GPT-4.1-mini o GPT-4.1 (según plan)
- Tablero kanban para flujo borrador → aprobado → publicado
- Programación automática de publicaciones con APScheduler
- Analytics de métricas por bot (engagement, impresión, frecuencia)
- Multi-tenant: usuarios con planes Free / Starter / Pro / Agency
- Billing y webhooks vía Stripe

**Lo que TweetBot tiene que CLAW no tiene hoy:**
- UI de gestión de contenido por canal específico (X)
- Modelo multi-tenant completo (auth, planes, billing)
- Kanban de aprobación humana antes de publicar
- 70 agentes IA especializados en generación de contenido social

---

### 2. `trading-bot-v4-pro` — Motor de Trading RL

| Atributo | Detalle |
|---|---|
| Repositorio | https://github.com/ariaslopez/trading-bot-v4-pro |
| Estado actual | Motor completo; sin capa web/API |
| Stack | Python + PPO+LSTM (Stable Baselines3) + MetaTrader 5 + Telegram |
| Función en CLAW | Motor de ejecución cuantitativa y backtest |
| Pipeline CLAW objetivo | `trading` |
| MCP a crear en CLAW | `trading_engine` |

**Capacidades disponibles para CLAW:**
- Agente PPO con LSTM para captura de dependencias temporales
- Reward shaping avanzado: Sharpe Ratio + penalizaciones por drawdown
- Feature engineering con análisis de sentimiento opcional
- Gestión de riesgo: circuit breakers, trailing stops, posición dinámica
- Filtros de régimen de mercado (`filters/`)
- Reentrenamiento programado: `retrain_scheduler.py`, `retrain_weekly.py`
- Watchdog de supervisión del bot (`watchdog.py`)
- Notificaciones Telegram (`notifications/`)

**Lo que TradingBot tiene que el pipeline TRADING de CLAW no tiene hoy:**
- Motor RL real con PPO+LSTM (CLAW tiene solo análisis y asesoría)
- Ejecución real de órdenes en MetaTrader 5
- Reentrenamiento automático programado
- Watchdog de supervisión continua

---

## Plan de integración — fases

### Fase 20-A: API interna de TradingBot ← primer paso recomendado

> **Pre-requisito:** Pipeline TRADING de CLAW auditado (post-Fase 14).

Objetivo: envolver `trading-bot-v4-pro` en una API REST interna mínima para que CLAW pueda controlarlo.

**Archivos a crear en `trading-bot-v4-pro`:**

```
trading-bot-v4-pro/
└── api/
    ├── server.py           # FastAPI / Flask mínimo
    ├── routes/
    │   ├── sessions.py     # POST /sessions, GET /sessions/{id}
    │   ├── metrics.py      # GET /sessions/{id}/metrics
    │   └── control.py      # POST /sessions/{id}/start|stop|pause
    └── schemas.py          # Pydantic models
```

**Endpoints mínimos necesarios:**

| Método | Ruta | Descripción |
|---|---|---|
| `POST` | `/sessions` | Crear sesión de trading (symbol, strategy, risk_params) |
| `GET` | `/sessions/{id}` | Estado de la sesión (running, paused, stopped) |
| `GET` | `/sessions/{id}/metrics` | Sharpe, drawdown, win_rate, PnL, equity_curve |
| `POST` | `/sessions/{id}/start` | Iniciar/reanudar sesión |
| `POST` | `/sessions/{id}/stop` | Detener sesión |
| `GET` | `/health` | Health check del motor |

---

### Fase 20-B: MCP `trading_engine` en CLAW

> **Pre-requisito:** API interna de TradingBot operativa (Fase 20-A).

**Archivo a crear en CLAW:** `infrastructure/mcps/trading_engine_mcp.py`

```python
# Herramientas que expone el MCP al MCPHub de CLAW
TOOLS = [
    "create_session",       # Lanza una sesión de trading
    "get_session_status",   # Estado actual del bot
    "get_session_metrics",  # Métricas de performance
    "control_session",      # start | stop | pause
    "list_sessions",        # Historial de sesiones
]
```

**Integración en `infrastructure/mcp_hub.py`:**
```python
# Añadir en MCP_REGISTRY
"trading_engine": {
    "base_url": os.getenv("TRADING_ENGINE_URL", "http://localhost:8001"),
    "timeout": 30,
    "rate_limit": None,  # API interna, sin rate limit externo
}
```

**Variable de entorno a añadir en `.env.example`:**
```env
TRADING_ENGINE_URL=http://localhost:8001
TRADING_ENGINE_API_KEY=
```

---

### Fase 20-C: API interna de TweetBot

> **Pre-requisito:** TweetBot Platform completa sus Fases 9–12 (motor de publicación real).

TweetBot ya tiene una API Flask robusta; solo hay que añadir endpoints internos específicos
para que CLAW los consuma sin pasar por la UI de usuario.

**Endpoints internos a crear en `twitter-bot-platform`:**

| Método | Ruta | Descripción |
|---|---|---|
| `POST` | `/internal/campaigns` | Crear campaña (bots, personalidad, schedule) |
| `POST` | `/internal/campaigns/{id}/generate` | Generar lote de tweets con IA |
| `GET` | `/internal/campaigns/{id}/queue` | Tweets en cola (kanban) |
| `POST` | `/internal/campaigns/{id}/approve-all` | Aprobar y programar todos los tweets |
| `GET` | `/internal/bots/{id}/metrics` | Métricas del bot (engagement, publicaciones) |
| `GET` | `/internal/health` | Health check del servicio |

---

### Fase 20-D: MCP `x_tweetbot` en CLAW

> **Pre-requisito:** Endpoints internos de TweetBot operativos (Fase 20-C).

**Archivo a crear en CLAW:** `infrastructure/mcps/x_tweetbot_mcp.py`

```python
TOOLS = [
    "create_campaign",      # Campaña de X con personalidad IA
    "generate_tweet_batch", # Generar tweets con GPT
    "get_content_queue",    # Estado del kanban
    "approve_and_schedule", # Aprobar y programar publicaciones
    "get_bot_metrics",      # Analytics del bot
]
```

**Variable de entorno a añadir en `.env.example`:**
```env
TWEETBOT_URL=http://localhost:5000
TWEETBOT_INTERNAL_API_KEY=
```

---

### Fase 20-E: Dashboard unificado en CLAW

> **Pre-requisito:** Fase 15 (Dashboard base) + MCPs `trading_engine` y `x_tweetbot` activos.

Añadir secciones al dashboard de CLAW en `ui/index.html`:

**Panel "Bots de Trading":**
- Instancias activas (symbol, estado, uptime)
- PnL acumulado y equity curve (sparkline)
- Drawdown máximo y Sharpe en tiempo real
- Botones start/stop/pause por sesión

**Panel "Bots de X":**
- Campañas activas (bot, personalidad, frecuencia)
- Tweets publicados hoy vs. programados
- Métricas de engagement (likes, retweets, impresiones)
- Acceso rápido al kanban de TweetBot

**Panel de cross-intelligence (futuro):**
- Usar señales de trading para generar posts en X automáticamente
  (ej: "Performance update: BTC +3.2% hoy — estrategia PPO en verde")
- Triggers: cierre de sesión de trading → agente CONTENT → campaña en X

---

## Decisión sobre la UI de TweetBot en CLAW

**Pregunta:** ¿Se reutiliza la UI de TweetBot como interfaz de X dentro del dashboard de CLAW?

**Respuesta:** La UI de TweetBot **sirve como interfaz operativa de X**, pero como micro-frontend
independiente, no embebida en el servidor FastAPI de CLAW. Las razones:

| Criterio | TweetBot UI incrustada | TweetBot UI como app hermana |
|---|---|---|
| Complejidad de integración | Alta — mezcla Flask + FastAPI | Baja — iframe o enlace profundo |
| Independencia de deploy | ❌ Acoplada | ✅ Desplegable por separado |
| UX unificada | ✅ | Parcial (cambio de contexto) |
| Riesgo de regresión | Alto | Bajo |
| **Recomendación a corto plazo** | — | ✅ **Esta opción** |
| **Recomendación a largo plazo** | — | Extraer componentes clave a frontend unificado (React + Tailwind) |

**Estrategia de transición:**
1. Corto plazo: enlace profundo desde CLAW dashboard → TweetBot UI (app hermana)
2. Medio plazo: iFrame controlado o redirección con contexto compartido (JWT)
3. Largo plazo: componentes Vue/React compartidos entre CLAW y TweetBot en un monorepo de frontend

---

## Roadmap de integración — timeline

```
Mayo 2026           Junio 2026          Q3 2026              Q4 2026
────────────────    ────────────────    ─────────────────    ──────────────────
Fase 14 ✅          Fase 15 Dashboard   Fase 20-A            Fase 20-D
Fase 15 Dashboard → Fase 16 Autonomía   TradingBot API       TweetBot MCP
                                        Fase 20-B            Fase 20-E
                                        trading_engine MCP   Dashboard unificado
                                        Fase 20-C
                                        TweetBot API interna
```

---

## Dependencias entre proyectos

```
orquestador-multiagente
    └── Fase 14 completa ──────────────────────────── (bloqueante)
    └── Fase 15 Dashboard ─────────────────────────── (bloqueante para Fase 20-E)
    └── Auditoría pipeline TRADING ────────────────── (bloqueante para Fase 20-B)

trading-bot-v4-pro
    └── API interna (Fase 20-A) ───────────────────── (bloqueante para Fase 20-B)

twitter-bot-platform
    └── Fase 9 completa (motor publicación) ───────── (bloqueante para Fase 20-C)
    └── Fases 10-12 completas ──────────────────────── (recomendado para Fase 20-D)
```

---

## Notas de arquitectura

- **No fusionar repositorios.** Cada proyecto tiene ciclos de deploy, tests y responsabilidades distintos.
- **Comunicación via HTTP interno.** Los MCPs en CLAW llaman a los servicios por HTTP. En producción, en la misma red privada (Docker network o VPC).
- **Auth entre servicios:** usar API keys internas (`X-Internal-Key`) para las rutas `/internal/`. No exponer estas rutas al exterior.
- **Observabilidad compartida:** los servicios externos deben emitir logs estructurados JSON que CLAW pueda consumir y mostrar en su dashboard.
- **Supabase como capa de datos compartida:** tanto TweetBot como CLAW usan Supabase. A largo plazo, definir schemas separados por servicio para evitar colisiones de tablas.
