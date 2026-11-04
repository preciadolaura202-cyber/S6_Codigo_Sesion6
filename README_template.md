# 💄 LAUPRÉA BEAUTY — Asistente Virtual

> Agente de IA para la venta de maquillaje, skincare y accesorios por catálogo.

## Descripción

LAUPRÉA BEAUTY es una marca que vende maquillaje por catálogo a través de asesoras y canales digitales. Este agente responde consultas de clientas y del equipo comercial sobre catálogo, precios, stock, envíos, devoluciones y pedidos, y además analiza las ventas y genera reportes ejecutivos.

## 🚀 Demo en vivo

- **Interfaz de chat:** `https://tu-proyecto.railway.app/`
- **API en producción:** `https://tu-proyecto.railway.app/api`
- **Documentación Swagger:** `https://tu-proyecto.railway.app/docs`
- **Estado del servicio:** `https://tu-proyecto.railway.app/health`

## 🧠 Capacidades del agente

Un solo endpoint (`POST /chat`) con un **coordinador (LangGraph)** que decide
automáticamente qué camino tomar según la pregunta — resume todo el curso:

| Camino | Se activa cuando... | Concepto del curso |
|---|---|---|
| **conversación** | saludos, cálculos, clima, hora, preguntas generales | Memoria + Herramientas (Sesiones 1-3) |
| **documentos** | preguntas sobre catálogo, precios, stock, envíos, devoluciones y pedidos | RAG sobre PDFs/CSV reales (Sesión 4) |
| **análisis** | "analiza", "compara", "investiga", "evalúa" | Equipo Investigador→Analista→Redactor (Sesión 4) |
| **reporte** | "genera un reporte", "informe ejecutivo" | Salida Estructurada con Pydantic (Sesión 2) |

## 📋 Endpoints disponibles

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/` | Interfaz de chat (frontend/index.html) |
| GET | `/api` | Información básica de la API, en JSON |
| GET | `/health` | Estado del servicio |
| GET | `/health/detail` | Estado detallado con herramientas |
| POST | `/chat` | Conversar con el agente (memoria + coordinador) |
| POST | `/agent` | Ejecutar tarea específica |
| DELETE | `/chat/{session_id}` | Limpiar historial de sesión |

## 🛠️ Tecnologías

- **LLM:** Groq (openai/gpt-oss-120b)
- **Framework agente:** LangChain (`create_agent`, `with_structured_output`) + LangGraph (coordinador)
- **RAG:** búsqueda híbrida por palabras clave sobre `data/documentos/` (PDFs + CSV), sin dependencias pesadas de embeddings
- **API REST:** FastAPI + Uvicorn
- **Despliegue:** Railway
- **Lenguaje:** Python 3.11

## ⚡ Ejemplo de uso

```bash
# Conversar con el agente
curl -X POST https://tu-proyecto.railway.app/chat \
  -H "Content-Type: application/json" \
  -d '{"mensaje": "¿Cuánto cuesta el labial Velvet Rose?", "session_id": "clienta_01"}'
```

```json
{
  "respuesta": "El labial Velvet Rose cuesta $42.900 COP y está disponible en el catálogo Primavera-Verano 2026.",
  "session_id": "clienta_01",
  "modelo": "openai/gpt-oss-120b"
}
```

## 🏃 Ejecutar localmente

```bash
# 1. Clonar el repositorio
git clone https://github.com/tu-usuario/tu-repo.git
cd "D:\Sesion 6\Sesion 6\files\LauraQuiroz-LAUPRÉA BEAUTY"

# 2. Crear entorno virtual
conda create -n agentes python=3.11 -y
conda activate agentes

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar variables de entorno
cp .env.example .env
# Editar .env con tus claves

# 5. Arrancar el servidor
uvicorn main:app --reload --port 8000

# 6. Ver documentación
# Abre http://localhost:8000/docs
```

## 🔧 Variables de entorno requeridas

| Variable | Descripción | Requerida |
|----------|-------------|-----------|
| `GROQ_API_KEY` | Clave de API de Groq | ✅ |
| `GROQ_MODEL` | Modelo para conversación/RAG/análisis | ✅ |
| `GROQ_MODEL_ESTRUCTURADO` | Modelo para el nodo "reporte" (salida estructurada) | ✅ |
| `AGENT_NAME` | Nombre del agente | ✅ |
| `AGENT_ROLE` | Rol y especialización | ✅ |
| `LLM_PROVIDER` | `groq` o `ollama` | ✅ |
| `MEMORY_TYPE` | `buffer` o `window` | ✅ |
| `MEMORY_WINDOW_SIZE` | Mensajes a recordar si `MEMORY_TYPE=window` | Opcional |
| `DOCUMENTOS_DIR` | Carpeta con los PDFs/CSV del RAG | ✅ |
| `TAMANO_FRAGMENTO` / `SUPERPOSICION_FRAGMENTO` / `K_FRAGMENTOS` | Ventana de contexto del RAG | Opcional |
| `OPENWEATHER_API_KEY` | API de clima | Opcional |

## 📁 Estructura del proyecto

```
├── main.py                   # Servidor FastAPI — sirve el frontend y la API
├── s6_llm_factory.py         # Crea el LLM (Groq/Ollama, temperatura, modelo por nodo)
├── Procfile                  # Instrucción de arranque para Railway
├── railway.toml              # Configuración de Railway
├── requirements.txt          # Dependencias Python
├── .env.example               # Plantilla de variables de entorno
├── data/documentos/           # PDFs + CSV reales que lee el RAG
├── frontend/index.html        # Interfaz de chat (un solo archivo)
├── core/
│   ├── agent_core.py         # Orquesta el grafo + memoria por sesión
│   ├── graph.py              # El coordinador LangGraph (4 caminos)
│   ├── rag.py                # Motor de RAG (búsqueda híbrida)
│   ├── tools.py              # Herramientas del agente
│   └── structured.py         # Esquemas Pydantic (salida estructurada)
├── models/
│   └── schemas.py            # Modelos Pydantic de la API
└── routes/
    ├── chat.py               # POST /chat, DELETE /chat/{session_id}
    ├── agent.py               # POST /agent
    └── health.py               # GET /health, /health/detail
```

## 👤 Autor

**[Tu nombre]**
- Seminario: Agentes de IA — Diseño, Integración y Despliegue en la Nube
- [Tu institución / organización]

---

*Proyecto desarrollado como parte del seminario de Agentes de IA.*
