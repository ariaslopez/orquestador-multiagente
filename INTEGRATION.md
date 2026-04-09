# CLAW Agent System — Documentación de Integración CLAW × Tweet Bot Platform

> **Versión:** v2.4.0 · **Fecha:** Abril 2026 · **Estado:** Implementado / En espera de activación

---

## Índice

1. [Visión general](#1-visión-general)
2. [Arquitectura de la integración](#2-arquitectura-de-la-integración)
3. [Agente responsable del contenido](#3-agente-responsable-del-contenido)
4. [Personalidades y prompts master](#4-personalidades-y-prompts-master)
5. [Endpoint `POST /api/orchestrator/tweet`](#5-endpoint-post-apiorchestratortweetle)
6. [Modelos de datos](#6-modelos-de-datos)
7. [Seguridad y autenticación](#7-seguridad-y-autenticación)
8. [Feature flag — activación controlada](#8-feature-flag--activación-controlada)
9. [Flujo completo paso a paso](#9-flujo-completo-paso-a-paso)
10. [TODO pendiente antes de activar](#10-todo-pendiente-antes-de-activar)
11. [Referencia rápida — variables de entorno](#11-referencia-rápida--variables-de-entorno)

---

## 1. Visión general

La integración conecta el **orquestador CLAW** (este repo) con la
**Tweet Bot Platform** (`twitter-bot-platform`) para que el agente
especializado `marketing-twitter-engager` genere el contenido de cada tweet
y la plataforma de bots lo publique en Twitter/X.

```
CLAW Orchestrator
  └── Pipeline: MARKETING (o cualquier pipeline que dispare contenido en X)
        └── Agente: marketing-twitter-engager
              │  genera TwitterContentPayload
              ▼
        POST /api/orchestrator/tweet   ← este repo (ui/server.py)
              │
              ▼
        Tweet Bot Platform
          └── Publica / programa el tweet
```

**Premisa de diseño:**
- CLAW decide el contenido (personalidad, tono, texto, alternativas, hilos).
- La plataforma de bots ejecuta la publicación (colas, límites de plan,
  horarios, logging en Supabase, Tweepy).

---

## 2. Arquitectura de la integración

```
┌──────────────────────────────────────────────────────────────┐
│  CLAW Agent System  (orquestador-multiagente)                │
│                                                              │
│  ┌─────────────────────────────────────┐                     │
│  │  marketing-twitter-engager          │                     │
│  │  · Recibe: topic + personalidad     │                     │
│  │  · Genera: TwitterContentPayload    │                     │
│  └────────────────┬────────────────────┘                     │
│                   │  POST /api/orchestrator/tweet            │
│                   │  Headers:                                │
│                   │    Authorization: Bearer <SECRET>        │
│                   │    X-Bot-Id: <bot_id>                    │
│                   │  Body: OrchestratorTweetPayload          │
└───────────────────┼──────────────────────────────────────────┘
                    │
                    ▼
┌──────────────────────────────────────────────────────────────┐
│  Tweet Bot Platform  (twitter-bot-platform)                  │
│                                                              │
│  ui/server.py                                                │
│  ├── Guard: CLAW_INTEGRATION_ENABLED=true                    │
│  ├── Guard: Authorization Bearer token                       │
│  ├── Guard: payload.status != "error"                        │
│  ├── Guard: len(tweet.text) <= 280                           │
│  ├── AuditLogger.log(event=orchestrator_tweet_received)      │
│  └── → Supabase platform_tweets (TODO Fase CLAW)            │
└──────────────────────────────────────────────────────────────┘
```

---

## 3. Agente responsable del contenido

### `marketing-twitter-engager`

| Campo         | Valor                                  |
|---------------|----------------------------------------|
| Repo fuente   | `agency-agents`                        |
| Pipeline      | `MARKETING`                            |
| Modelo base   | `gpt-4.1-mini` (configurable)          |
| Entrada       | topic + personalidad + restricciones   |
| Salida        | `OrchestratorTweetPayload` (JSON)      |

**Responsabilidades:**
- Generar el tweet principal (`tweet.text`, max 280 chars).
- Generar hasta 3 alternativas (`alternatives[]`).
- Generar hilo opcional (`thread[]`).
- Seleccionar personalidad alineada con el segmento objetivo.
- Incluir metadatos de trazabilidad (`meta.trace_id`, `meta.pipeline_name`,
  `meta.tokens_used`).

**Lo que NO hace:**
- No ejecuta la publicación en Twitter/X.
- No maneja colas ni límites de plan.
- No persiste en Supabase.

---

## 4. Personalidades y prompts master

Las personalidades definen el carácter con el que `marketing-twitter-engager`
genera cada tweet. Cada personalidad tiene cuatro campos:
`name`, `tone`, `style` e `instructions`.

El campo `instructions` es el **prompt master** de comportamiento. Es el más
importante: define reglas estrictas que el agente debe seguir en cada
generación.

---

### 4.1 `profesional`

```python
{
    "name": "profesional",
    "tone": "authoritative",
    "style": "clear, data-driven, no fluff",
    "instructions": (
        "Te posicionas como una voz de referencia en el sector. "
        "Tu objetivo es aportar claridad y criterio en cada tweet, "
        "resumiendo ideas complejas de forma precisa y sin adornos innecesarios. "
        "Evita exageraciones y promesas vacías; prioriza datos, matices y "
        "conclusiones accionables. No uses emojis salvo en casos muy justificados "
        "y nunca abuses de mayúsculas o signos de exclamación."
    ),
}
```

---

### 4.2 `educativo`

```python
{
    "name": "educativo",
    "tone": "informative",
    "style": "step-by-step, examples, analogies",
    "instructions": (
        "Tu misión es enseñar. Descompones conceptos complejos en pasos sencillos, "
        "usando ejemplos concretos y analogías que cualquiera pueda entender. "
        "Cada tweet debe dejar al lector con una idea clara, una mini-lección o "
        "un marco mental práctico. Evita tecnicismos sin explicar; cuando uses "
        "jerga, añádela con una breve explicación."
    ),
}
```

---

### 4.3 `humorístico`

```python
{
    "name": "humoristico",
    "tone": "witty",
    "style": "light irony, relatable observations",
    "instructions": (
        "Tu objetivo es entretener sin perder inteligencia. Usas humor, ironía ligera "
        "y observaciones cotidianas, sin cruzar líneas de respeto ni convertirte en "
        "un meme vacío. Los chistes deben conectar con la realidad del público "
        "(trabajo, tecnología, negocio, vida diaria) y nunca atacar colectivos "
        "vulnerables. Emojis OK, pero úsalos como remate, no como sustituto del "
        "contenido."
    ),
}
```

---

### 4.4 `motivacional`

```python
{
    "name": "motivacional",
    "tone": "inspiring",
    "style": "action-oriented, micro-stories, real examples",
    "instructions": (
        "Buscas inspirar acción real, no vender humo. Combinas mensajes motivacionales "
        "con ejemplos concretos, micro-historias y pequeños retos que el lector pueda "
        "aplicar hoy mismo. Evita frases cliché sin contexto; siempre que des una frase "
        "potente, acompáñala con una situación o ejemplo. Puedes usar emojis positivos "
        "con moderación para reforzar el tono."
    ),
}
```

---

### 4.5 `controversial`

```python
{
    "name": "controversial",
    "tone": "bold",
    "style": "strong opinion + reasoning, debate-inviting",
    "instructions": (
        "Tu función es abrir debates inteligentes, no generar polémica vacía. "
        "Formula opiniones fuertes pero razonadas, dejando claro el porqué y "
        "reconociendo matices cuando existan. Evita ataques personales, insultos o "
        "lenguaje discriminatorio. Idealmente cada tweet debe terminar con una pregunta "
        "o invitación al debate para fomentar respuestas."
    ),
}
```

---

### 4.6 `noticias`

```python
{
    "name": "noticias",
    "tone": "neutral",
    "style": "concise, sourced, journalistic",
    "instructions": (
        "Actúas como un micro-medio informativo. Resumes noticias y novedades de forma "
        "breve, clara y neutral, señalando por qué son relevantes para el lector. "
        "Cuando sea posible, contextualiza: qué ha cambiado, a quién afecta, qué puede "
        "pasar después. Evita clickbait y opiniones personales; si mencionas una fuente, "
        "hazlo de forma explícita (\"según X\")."
    ),
}
```

---

### 4.7 Prompt master de generación (`system_prompt`)

Este es el prompt genérico que **envuelve** las instrucciones de la personalidad
en cada llamada al LLM:

```python
system_prompt = f"""
Eres {name}, un bot de Twitter/X con personalidad {tone}.
{f"Estilo recomendado: {style}." if style else ""}
{f"Guía de comportamiento: {instructions}" if instructions else ""}

Reglas estrictas:
- Escribe SOLO el contenido del tweet, sin comillas, sin explicaciones
  y sin prefijos como "Tweet:".
- Máximo 280 caracteres.
- Escribe en {language}.
- Mantén coherencia con el tono indicado ({tone}) y la guía de comportamiento.
- Prioriza claridad, originalidad y valor para el lector.
- No añadas hashtags salvo que sean naturales y realmente aporten contexto.
""".strip()

user_prompt = f"{topic_line}\nGenera un único tweet original listo para publicar."
```

---

### 4.8 Prompt master de reescritura (`rewrite_tweet`)

```python
system_prompt = f"""
Eres {name}, un experto en redacción para Twitter/X con tono {tone}.

Tu tarea es mejorar el siguiente tweet según las instrucciones dadas.

Reglas estrictas:
- Escribe SOLO el tweet mejorado, sin comillas ni explicaciones adicionales.
- Máximo 280 caracteres.
- Escribe en {language}.
- Mantén el tono indicado ({tone}) y la intención original del mensaje.
- No inventes hechos nuevos ni cambies el significado de fondo.
- No añadas prefijos como "Tweet:" ni notas entre paréntesis.
""".strip()
```

---

## 5. Endpoint `POST /api/orchestrator/tweet`

### Descripción

Recibe el `OrchestratorTweetPayload` generado por `marketing-twitter-engager`
y lo encola o programa en la plataforma de bots para publicación en Twitter/X.

### URL

```
POST http://<host>/api/orchestrator/tweet
```

### Estado

**INACTIVO** hasta que `CLAW_INTEGRATION_ENABLED=true` esté configurado.
El endpoint devuelve `HTTP 503` y está oculto en `/docs` mientras esté inactivo.

### Headers requeridos

| Header          | Tipo   | Descripción                              |
|-----------------|--------|------------------------------------------|
| `Authorization` | string | `Bearer <ORCHESTRATOR_SECRET>`           |
| `X-Bot-Id`      | string | (opcional) ID del bot destino en la BD   |

### Guards (en orden de ejecución)

| # | Guard                | Código HTTP | Condición                                |
|---|----------------------|-------------|------------------------------------------|
| 1 | Feature flag         | `503`       | `CLAW_INTEGRATION_ENABLED=false`         |
| 2 | Autenticación        | `401`       | Token Bearer incorrecto o ausente        |
| 3 | Payload del agente   | `422`       | `payload.status == "error"`              |
| 4 | Longitud del tweet   | `422`       | `len(tweet.text) > 280`                  |
| 5 | AuditLogger          | —           | Log silencioso; no bloquea si falla      |

### Respuesta exitosa (`200 OK`)

```json
{
  "tweet_id": "uuid-v4",
  "status": "queued | scheduled",
  "publish_at": "2026-04-10T14:00:00Z | null",
  "message": "Tweet encolado para publicación automática. trace_id=abc-123"
}
```

---

## 6. Modelos de datos

### `OrchestratorTweetPayload` (input)

```python
class OrchestratorTweetPayload(BaseModel):
    status: str                    # "ok" | "error"
    tweet: OrchestratorTweetContent
    alternatives: list[str] = []  # hasta 3 alternativas
    thread: list[str] = []        # tweets de hilo ordenados
    scheduling: OrchestratorScheduling
    meta: OrchestratorMeta
    error: Optional[str] = None   # mensaje de error si status="error"
```

### `OrchestratorTweetContent`

```python
class OrchestratorTweetContent(BaseModel):
    text: str            # contenido final del tweet (max 280 chars)
    char_count: int      # calculado por el agente
    language: str        # "es" | "en" | etc.
    personality_used: str  # nombre de la personalidad seleccionada
```

### `OrchestratorScheduling`

```python
class OrchestratorScheduling(BaseModel):
    publish_at: Optional[str] = None  # ISO 8601 o null (= publicar inmediato)
    timezone: str = "America/Bogota"
```

### `OrchestratorMeta`

```python
class OrchestratorMeta(BaseModel):
    pipeline_name: str      # nombre del pipeline CLAW que generó el contenido
    trace_id: str           # UUID de trazabilidad end-to-end
    tokens_used: int = 0    # tokens consumidos por el agente
    model: str = "gpt-4.1-mini"
```

### `OrchestratorTweetResponse` (output)

```python
class OrchestratorTweetResponse(BaseModel):
    tweet_id: str           # UUID generado por la plataforma
    status: str             # "queued" | "scheduled" | "published" | "error"
    publish_at: Optional[str] = None
    message: str            # descripción legible + trace_id para logs
```

---

## 7. Seguridad y autenticación

### Modelo de autenticación

La integración usa un **shared secret** (Bearer token) entre CLAW y la
plataforma. Es adecuado para comunicación interna server-to-server en la
misma infraestructura o VPC.

```
CLAW → Authorization: Bearer <ORCHESTRATOR_SECRET> → Tweet Bot Platform
```

### Reglas de seguridad

1. `ORCHESTRATOR_SECRET` debe ser un token aleatorio de al menos 32 caracteres.
   Generarlo con: `python -c "import secrets; print(secrets.token_hex(32))"`.
2. Nunca commitear el valor en el repo. Usar `.env` local o Fly.io secrets.
3. Si `ORCHESTRATOR_SECRET` está vacío, el endpoint devuelve `503` por diseño.
4. En Fase 19 (producción), escalar a JWT con expiración y `RS256`.

### Configuración en Fly.io

```bash
fly secrets set \
  CLAW_INTEGRATION_ENABLED=true \
  ORCHESTRATOR_SECRET=$(python -c "import secrets; print(secrets.token_hex(32))") \
  -a <nombre-de-la-app>
```

---

## 8. Feature flag — activación controlada

La integración está **desactivada por defecto** mediante dos variables de entorno:

| Variable                   | Default  | Efecto cuando está en `true`                           |
|----------------------------|----------|--------------------------------------------------------|
| `CLAW_INTEGRATION_ENABLED` | `false`  | Activa el endpoint y lo muestra en `/docs`             |
| `ORCHESTRATOR_SECRET`      | `""`     | Token que CLAW debe enviar en `Authorization: Bearer`  |

### Indicador en `/api/health`

```json
{
  "status": "ok",
  "version": "2.4.0",
  "claw_integration": false
}
```

El campo `claw_integration` permite que el dashboard y el propio CLAW sepan
el estado actual sin leer variables de entorno directamente.

### Activación paso a paso

```bash
# 1. Local (.env)
CLAW_INTEGRATION_ENABLED=true
ORCHESTRATOR_SECRET=tu-token-secreto-aqui

# 2. Verificar que /api/health devuelve "claw_integration": true
curl http://127.0.0.1:8000/api/health

# 3. Probar el endpoint con un payload de ejemplo
curl -X POST http://127.0.0.1:8000/api/orchestrator/tweet \
  -H "Authorization: Bearer tu-token-secreto-aqui" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "ok",
    "tweet": {
      "text": "La IA no va a reemplazarte. Va a reemplazar a quien no sepa usarla.",
      "char_count": 65,
      "language": "es",
      "personality_used": "controversial"
    },
    "alternatives": [],
    "thread": [],
    "scheduling": { "publish_at": null, "timezone": "America/Bogota" },
    "meta": {
      "pipeline_name": "MARKETING",
      "trace_id": "trace-001",
      "tokens_used": 342,
      "model": "gpt-4.1-mini"
    }
  }'
```

---

## 9. Flujo completo paso a paso

```
Usuario / Trigger externo
  │
  │  describe objetivo de campaña + segmento + personalidad
  ▼
CLAW Orchestrator
  │  clasifica → Pipeline MARKETING
  ▼
marketing-twitter-engager (agency-agents)
  │  · Lee personalidad e instructions del DEFAULT_PERSONALITIES
  │  · Construye system_prompt + user_prompt
  │  · Llama al LLM (gpt-4.1-mini o configurado)
  │  · Valida: len(text) <= 280, language, personality_used
  │  · Construye OrchestratorTweetPayload
  ▼
POST /api/orchestrator/tweet
  │
  ├── Guard 1: CLAW_INTEGRATION_ENABLED ─── false → 503
  ├── Guard 2: Bearer token ────────────── inválido → 401
  ├── Guard 3: payload.status ──────────── "error" → 422
  ├── Guard 4: len(tweet.text) ─────────── > 280 → 422
  │
  ├── AuditLogger.log(orchestrator_tweet_received)
  │
  ├── scheduling.publish_at ?
  │   ├── sí → status = "scheduled"
  │   └── no → status = "queued"
  │
  └── OrchestratorTweetResponse { tweet_id, status, publish_at, message }
        │
        ▼  (TODO Fase CLAW)
  Supabase: platform_tweets
        │
        ▼
  Worker / Scheduler de bots
        │
        ▼
  Twitter/X API (Tweepy)
```

---

## 10. TODO pendiente antes de activar

Los siguientes ítems deben completarse antes de poner
`CLAW_INTEGRATION_ENABLED=true` en producción:

### Fase CLAW (Twitter Bot Platform — Fases 9-12)

- [ ] **Supabase `platform_tweets`**: persistir el payload recibido con campos:
  ```
  tweet_id, bot_id, text, personality_used, language,
  alternatives, thread_tweets, orchestrator_trace_id,
  pipeline_name, tokens_used, model_used,
  publish_at, status, received_at
  ```
- [ ] **Worker de publicación real**: leer de `platform_tweets` con
  `status=queued` y publicar vía Tweepy.
- [ ] **Endpoint `/internal/`** en `twitter-bot-platform`:
  campaigns, generate, queue, approve-all, metrics
  (requerido para Fase 20-C).

### Fase 20-D (CLAW — MCPs)

- [ ] `infrastructure/mcps/x_tweetbot_mcp.py`
- [ ] Herramientas: `create_campaign`, `generate_tweet_batch`,
  `get_content_queue`, `approve_and_schedule`
- [ ] Registrar en MCPHub + `.env.example` (`TWEETBOT_URL`)

### Producción (Fase 19)

- [ ] Reemplazar Bearer token por JWT con expiración + `RS256`
- [ ] Rate limiting en `/api/orchestrator/tweet` (max 60 req/min)
- [ ] Retry automático en worker si Tweepy falla

---

## 11. Referencia rápida — variables de entorno

```env
# ── Integración CLAW ──────────────────────────────────────────────────────────
# Desactivada por defecto. Activar SOLO cuando la integración esté completa.

CLAW_INTEGRATION_ENABLED=false
# Valores: true | false
# Efecto: activa POST /api/orchestrator/tweet y lo muestra en /docs

ORCHESTRATOR_SECRET=
# Valor: string aleatorio ≥ 32 chars
# Generar: python -c "import secrets; print(secrets.token_hex(32))"
# Nunca committear en el repo
```

---

*Última actualización: Abril 9, 2026 — Generado como parte de la sesión de trabajo v2.4.0*
