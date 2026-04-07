# 📖 Manual de Usuario — CLAW Agent System

> **Para quién es este manual:** cualquier persona que quiera usar el sistema, sin importar si sabe programar o no.
> **Versión actual:** v2.1.0 | **Última actualización:** Abril 2026

---

## ¿Qué es CLAW?

CLAW es un **asistente inteligente** que trabaja en tu computadora. Le das una tarea en español o inglés, y él la ejecuta solo, paso a paso, usando inteligencia artificial.

Es como tener un equipo de especialistas virtuales disponibles 24/7:
- Un **planificador** que organiza el trabajo
- Un **programador** que escribe código
- Un **revisor** que verifica la calidad
- Un **analista** que investiga información
- ...y más, según el tipo de tarea

Lo mejor: **funciona sin internet** usando tu propia computadora como cerebro principal.

---

## ✅ Instalación — Paso a Paso

### Paso 1: Instalar Python
Si no tienes Python instalado:
1. Ve a [python.org/downloads](https://python.org/downloads)
2. Descarga la versión **3.10 o superior**
3. Durante la instalación, marca la casilla **"Add Python to PATH"**
4. Haz clic en "Install Now"

**Verificar instalación:** Abre la terminal (cmd en Windows) y escribe:
```
python --version
```
Debe mostrar algo como `Python 3.11.x`

---

### Paso 2: Instalar Ollama (cerebro local)
Ollama es el programa que hace funcionar la IA en tu propia computadora, sin enviar datos a internet.

**En Windows:**
```
winget install Ollama.Ollama
```
O descárgalo desde [ollama.com](https://ollama.com)

**Descargar el modelo de IA:**
```
ollama pull qwen2.5-coder:7b-q4_K_M
```
> ⏱️ Esto descarga ~4.5 GB. Solo se hace una vez.

---

### Paso 3: Descargar CLAW
```
git clone https://github.com/ariaslopez/orquestador-multiagente.git
cd orquestador-multiagente
```

---

### Paso 4: Instalar dependencias
```
pip install -r requirements.txt
```

---

### Paso 5: Configuración inicial
Ejecuta el asistente de configuración automática:
```
python setup.py
```
El asistente te pedirá:
- 🔑 **Groq API Key** (gratis en [console.groq.com](https://console.groq.com)) — para tareas de investigación
- 🔑 **Gemini API Key** (gratis en [aistudio.google.com](https://aistudio.google.com)) — respaldo adicional
- Estas claves son opcionales pero mejoran la calidad en tareas complejas

---

### Paso 6: Verificar que todo funciona
```
python main.py --doctor
```
Deberías ver algo así:
```
✅ Ollama: activo (qwen2.5-coder:7b)
✅ Groq: conectado
✅ Gemini: conectado
✅ Sistema listo — v2.1.0
```

---

## 🚀 Uso Básico

### El comando principal
```
python main.py --task "tu tarea aquí" --type tipo_de_tarea
```

**Ejemplo real:**
```
python main.py --task "Crea una calculadora web" --type dev
```

CLAW hará todo el trabajo: planifica, escribe el código, lo revisa, lo prueba y lo guarda en la carpeta `output/`.

---

## 🎯 Los 12 Tipos de Tarea (Pipelines)

Elige el tipo según lo que necesitas hacer:

### 💻 `dev` — Desarrollo de Software
**¿Cuándo usarlo?** Cuando quieres crear o mejorar un programa, script, API, o cualquier cosa de código.
```
python main.py --task "Crea una API para gestionar inventario" --type dev
python main.py --task "Agrega autenticación a mi app Flask" --type dev
```
6 agentes trabajan en secuencia: Planificador → Programador → Revisor de código → Revisor de seguridad → Ejecutor → Git

---

### 🔍 `research` — Investigación
**¿Cuándo usarlo?** Cuando necesitas investigar un tema, buscar información, analizar fuentes.
```
python main.py --task "Investiga las mejores estrategias de trading algorítmico en 2026" --type research
python main.py --task "Analiza el mercado de criptomonedas esta semana" --type research
```
4 agentes: Buscador web → Recolector de datos → Analista → Redactor del reporte

---

### ✍️ `content` — Creación de Contenido
**¿Cuándo usarlo?** Posts para redes sociales, artículos de blog, emails, newsletters.
```
python main.py --task "Escribe 5 posts de LinkedIn sobre trading algorítmico" --type content
python main.py --task "Crea un artículo de blog sobre Python para finanzas" --type content
```

---

### 📄 `office` — Documentos de Trabajo
**¿Cuándo usarlo?** Reportes, presentaciones, resúmenes ejecutivos, propuestas.
```
python main.py --task "Crea un reporte ejecutivo de resultados Q1 2026" --type office
python main.py --task "Genera una propuesta comercial para servicios de IA" --type office
```

---

### 🧪 `qa` — Control de Calidad
**¿Cuándo usarlo?** Revisar y probar código existente, encontrar bugs, generar tests.
```
python main.py --task "Revisa y prueba este módulo de pagos" --type qa
python main.py --task "Genera tests unitarios para la función de backtest" --type qa
```

---

### 📈 `trading` — Análisis de Trading
**¿Cuándo usarlo?** Estrategias de trading, análisis técnico, señales, backtesting.
```
python main.py --task "Analiza la estrategia RSI + MACD para BTC/USDT" --type trading
python main.py --task "Diseña una estrategia de scalping para forex" --type trading
```

---

### 📋 `pm` — Gestión de Proyectos
**¿Cuándo usarlo?** Planificar proyectos, crear roadmaps, organizar tareas, sprints.
```
python main.py --task "Crea el roadmap para lanzar un SaaS de trading en 3 meses" --type pm
python main.py --task "Organiza las tareas del sprint de este mes" --type pm
```

---

### 📊 `analytics` — Análisis de Datos
**¿Cuándo usarlo?** Analizar datos, generar reportes con métricas, insights de negocio.
```
python main.py --task "Analiza estos datos de ventas y encuentra patrones" --type analytics
python main.py --task "Genera un dashboard de métricas para mi bot de trading" --type analytics
```

---

### 📣 `marketing` — Marketing
**¿Cuándo usarlo?** Estrategias de marketing, campañas, copy publicitario, SEO.
```
python main.py --task "Crea una campaña de email marketing para mi producto de IA" --type marketing
python main.py --task "Escribe copy para anuncios de Facebook de un servicio de trading" --type marketing
```

---

### 🎯 `product` — Diseño de Producto
**¿Cuándo usarlo?** Definir features, user stories, PRDs, especificaciones de producto.
```
python main.py --task "Define los features principales para una app de señales de trading" --type product
python main.py --task "Crea el PRD para un dashboard de análisis de portafolio" --type product
```

---

### 🔐 `security_audit` — Auditoría de Seguridad
**¿Cuándo usarlo?** Revisar código en busca de vulnerabilidades, malas prácticas de seguridad.
```
python main.py --task "Audita la seguridad de este endpoint de autenticación" --type security_audit
python main.py --task "Revisa si hay vulnerabilidades en mi API de pagos" --type security_audit
```
⚠️ Este pipeline usa Groq (cloud) para mayor capacidad de análisis.

---

### 🎨 `design` — Diseño UI/UX
**¿Cuándo usarlo?** Diseño de interfaces, sistemas de diseño, UX research, wireframes.
```
python main.py --task "Diseña la UI para un dashboard de trading" --type design
python main.py --task "Crea el sistema de diseño para una app fintech" --type design
```

---

## ⚙️ Opciones Avanzadas

### Ver el plan antes de ejecutar
```
python main.py --task "Crea una API de trading" --type dev --plan
```
CLAW te muestra qué va a hacer antes de hacer algo. Úsalo cuando la tarea es importante y quieres verificar el approach.

---

### Ejecutar sin confirmaciones (modo autónomo)
```
python main.py --task "Crea una API de trading" --type dev --auto
```
CLAW trabaja de principio a fin sin pedirte confirmaciones. Ideal cuando confías en la tarea.

---

### Controlar la profundidad de investigación
```
# Rápido y ligero (ahorra tiempo y recursos)
python main.py --task "..." --effort min

# Balance (por defecto)
python main.py --task "..." --effort normal

# Profundo y detallado (para tareas críticas)
python main.py --task "..." --effort max
```

---

### Referenciar archivos en tu tarea
```
python main.py --task "Mejora el rendimiento de @src/backtester.py" --type dev
```
CLAW leerá ese archivo y lo tendrá como contexto al trabajar.

---

### Pasar contenido por tubería (pipe)
```
cat mi_codigo.py | python main.py --type qa --stdin
git diff HEAD~1 | python main.py --type security_audit --stdin
```
Útil para pasar código o datos directamente desde la terminal.

---

### Modo interactivo
```
python main.py --interactive
```
Abre un loop donde puedes dar múltiples tareas una tras otra sin reescribir el comando.

---

### Dashboard visual en el navegador
```
python main.py --ui
```
Abre el dashboard en tu navegador: **http://127.0.0.1:8000**
Desde ahí puedes dar tareas y ver cómo trabaja cada agente en tiempo real.

---

## 📂 ¿Dónde están los resultados?

Todo lo que genera CLAW se guarda en:
```
orquestador-multiagente/
  output/
    nombre-del-proyecto/    ← carpeta creada automáticamente
      *.py                  ← código generado
      README.md             ← documentación del proyecto
      tests/                ← tests generados
      ...
```

---

## 🛠️ Comandos del Sistema

```bash
# Ver estado del sistema
python main.py --doctor

# Ver historial de tareas recientes
python main.py --history

# Ver tokens y costos acumulados
python main.py --usage

# Retomar una tarea interrumpida
python main.py --resume abc123

# Ver ayuda completa
python main.py --help
```

---

## ❓ Problemas Comunes y Soluciones

### ❌ "Ollama no está corriendo"
**Solución:** Abre Ollama manualmente:
- Windows: busca "Ollama" en el menú inicio y ábrelo
- O en terminal: `ollama serve`

---

### ❌ "No module named..."
**Solución:** Reinstala las dependencias:
```
pip install -r requirements.txt
```

---

### ❌ La tarea se demora mucho
**Razón:** Sin GPU dedicada, la IA corre en CPU (~4-7 palabras por segundo).
**Soluciones:**
- Usa `--effort min` para tareas simples
- Deja que corra en segundo plano
- Para tareas largas, usa `--auto` para que no espere confirmaciones tuyas

---

### ❌ "API Key no válida" (Groq o Gemini)
**Solución:** Edita el archivo `.env` y verifica que las claves estén correctas:
```
notepad .env          # Windows
nano .env             # Mac/Linux
```
Las claves gratuitas se obtienen en:
- Groq: [console.groq.com](https://console.groq.com)
- Gemini: [aistudio.google.com](https://aistudio.google.com)

---

### ❌ Los archivos generados no aparecen
**Solución:** Busca en la carpeta `output/` dentro del proyecto. Si diste un nombre de proyecto en la tarea, habrá una subcarpeta con ese nombre.

---

### ❌ El sistema genera código con errores
**Solución:**
1. Usa `--type qa` para que otro agente lo revise:
   ```
   python main.py --task "Revisa y corrige el código en output/mi-proyecto/" --type qa
   ```
2. O pasa el código con `--stdin`:
   ```
   cat output/mi-proyecto/main.py | python main.py --type qa --stdin
   ```

---

## 🔑 Resumen de claves API necesarias

| API | Necesaria | Cómo obtenerla | Límite gratuito |
|-----|-----------|----------------|------------------|
| Groq | Recomendada | [console.groq.com](https://console.groq.com) | 14,400 tokens/min |
| Gemini | Recomendada | [aistudio.google.com](https://aistudio.google.com) | 1M tokens/día |
| GitHub Token | Opcional | GitHub → Settings → Developer Settings | Según plan |
| Ollama | ✅ Incluido | Se instala en tu PC | Ilimitado (local) |

---

## 💡 Consejos para Mejores Resultados

1. **Sé específico** — Mejor `"Crea una API REST en FastAPI con endpoints para CRUD de usuarios con JWT"` que `"Crea una API"`

2. **Usa el tipo correcto** — Si quieres código, usa `dev`. Si quieres un reporte, usa `office`. El tipo determina qué equipo de agentes trabaja.

3. **Usa `--plan` primero** para tareas grandes — Verifica el enfoque antes de ejecutar.

4. **Revisa con `--type qa`** después de `--type dev` — El pipeline QA es tu segunda capa de revisión.

5. **Referencia archivos con `@`** — `"Mejora @src/strategy.py para incluir stop-loss dinámico"` es mucho más preciso que describir el archivo.

6. **Para tareas de trading** — El pipeline `trading` está optimizado para análisis técnico, mientras que `analytics` es mejor para datos históricos y métricas.

---

## 📋 Referencia rápida — Todos los comandos

```bash
# TAREAS
python main.py --task "..." --type dev|research|content|office|qa|trading|pm|analytics|marketing|product|security_audit|design

# MODIFICADORES
  --plan          Solo ver el plan, no ejecutar
  --auto          Ejecutar sin confirmaciones
  --effort min|normal|max   Profundidad de trabajo
  --stdin         Recibir contenido por pipe

# SESIONES
  --resume ID     Retomar sesión interrumpida
  --rewind ID     Revertir a checkpoint anterior
  --history       Ver últimas 20 sesiones

# SISTEMA
  --doctor        Diagnóstico del sistema
  --ui            Dashboard en navegador
  --interactive   Modo de múltiples tareas
  --usage         Ver tokens y costos
  --init /ruta    Analizar proyecto existente (próximamente)
  --help          Ver toda la ayuda
```

---

## 🗺️ ¿Qué viene próximamente?

| Feature | Descripción | Cuándo |
|---------|-------------|--------|
| **Loop de corrección** | El sistema detecta errores y los corrige solo | v2.2.0 |
| **Analizar proyectos** | `--init` para que CLAW entienda tu proyecto existente | v2.3.0 |
| **Memoria** | CLAW recuerda lo que funcionó en tareas anteriores | v2.4.0 |
| **GPU rápida** | Con GPU dedicada, 10x más velocidad | v3.0.0 |

---

> 📬 **¿Tienes dudas o sugerencias?** Abre un issue en [github.com/ariaslopez/orquestador-multiagente](https://github.com/ariaslopez/orquestador-multiagente/issues)
>
> 🔄 **Este manual se actualiza automáticamente** con cada nueva versión del sistema.
