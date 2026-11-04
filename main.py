"""
============================================================
  main.py — Servidor FastAPI principal
  Seminario: Agentes de IA · Sesión 6 (Despliegue)

  Punto de entrada de la aplicación.
  Registra todos los routers, sirve el frontend de chat
  (frontend/index.html) y configura la API.

  Un solo despliegue en Railway sirve las dos cosas:
    - La interfaz de chat en  /
    - La API REST en          /chat, /agent, /health...
    - La documentación en     /docs

  Arrancar el servidor:
      uvicorn main:app --reload --port 8000

  Ver documentación Swagger:
      http://localhost:8000/docs

  ✏️ MODIFICA AQUÍ: título, descripción y versión de la API
============================================================
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

from routes.chat   import router as chat_router
from routes.agent  import router as agent_router
from routes.health import router as health_router

load_dotenv()

# ═══════════════════════════════════════════════════════════
#  ✏️ MODIFICA AQUÍ — Metadata de tu API
#  Esto aparece en la documentación Swagger
# ═══════════════════════════════════════════════════════════
NOMBRE_AGENTE = os.getenv("AGENT_NAME", "LAUPRÉA BEAUTY")

app = FastAPI(
    title=f"API — {NOMBRE_AGENTE}",
    description=f"""
## Asistente Inteligente: {NOMBRE_AGENTE} ✨

API REST del asistente virtual oficial y analítica de **LAUPRÉA BEAUTY S.A.S.**,
marca de maquillaje, skincare y accesorios de belleza por catálogo, fundada y diseñada
por **Laura Jimena Quiroz Preciado**.

Consulta catálogo en tiempo real, precios, stock, pedidos y políticas comerciales (RAG),
o genera análisis estratégicos de ventas y reportes ejecutivos estructurados.

### Endpoints disponibles:
- **POST /chat** — Conversar con el agente (con memoria, RAG, multiagente y salida estructurada)
- **POST /agent** — Ejecutar tareas específicas con contexto adicional
- **GET /health** — Verificar estado básico del servicio
- **GET /health/detail** — Estado detallado con herramientas y proveedor activo
- **DELETE /chat/{{session_id}}** — Limpiar memoria de conversación

### Documentación:
- Swagger UI: `/docs`
- ReDoc: `/redoc`
    """,
    version="1.2.0",
    # ✏️ Metadata del proyecto
    contact={
        "name":  "Laura Jimena Quiroz Preciado — LAUPRÉA BEAUTY",
        "email": "soporte@lauprea.com",
    },
    license_info={
        "name": "MIT",
    },
)

# ═══════════════════════════════════════════════════════════
#  CORS — permite que frontends externos llamen a la API
#  ✏️ MODIFICA AQUÍ: restringe los orígenes en producción
# ═══════════════════════════════════════════════════════════
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # ✏️ en producción: ["https://tusitioweb.com"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ═══════════════════════════════════════════════════════════
#  ROUTERS — registra todos los endpoints
# ═══════════════════════════════════════════════════════════
app.include_router(health_router, tags=["Monitoreo"])
app.include_router(chat_router,   tags=["Chat"])
app.include_router(agent_router,  tags=["Agente"])


# ═══════════════════════════════════════════════════════════
#  FRONTEND — sirve la interfaz de chat en la ruta raíz
#  El archivo vive en frontend/index.html; ver ese archivo
#  para modificar la interfaz visual del chat.
# ═══════════════════════════════════════════════════════════
FRONTEND_INDEX = Path(__file__).parent / "frontend" / "index.html"


@app.get("/", tags=["Info"])
async def root():
    """GET / — sirve la interfaz de chat (frontend/index.html)"""
    return FileResponse(FRONTEND_INDEX, media_type="text/html; charset=utf-8")


@app.get("/api", tags=["Info"])
async def info():
    """GET /api — información básica de la API, en JSON"""
    return {
        "api":      f"Agente IA — {NOMBRE_AGENTE}",
        "version":  "1.0.0",
        "docs":     "/docs",
        "health":   "/health",
    }


# ═══════════════════════════════════════════════════════════
#  ARRANQUE DIRECTO
#  Ejecuta con:  python main.py
#  O con:        uvicorn main:app --reload
# ═══════════════════════════════════════════════════════════
if __name__ == "__main__":
    import uvicorn
    host  = os.getenv("API_HOST", "0.0.0.0")
    port  = int(os.getenv("API_PORT", "8000"))
    debug = os.getenv("API_DEBUG", "True").lower() == "true"

    print(f"\n{'─'*50}")
    print(f"  🚀 Servidor arrancando...")
    print(f"  Agente:  {NOMBRE_AGENTE}")
    print(f"  URL:     http://localhost:{port}")
    print(f"  Docs:    http://localhost:{port}/docs")
    print(f"{'─'*50}\n")

    uvicorn.run("main:app", host=host, port=port, reload=debug)
