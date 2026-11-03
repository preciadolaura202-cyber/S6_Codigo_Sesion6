"""
core/agent_core.py — El agente completo, encapsulado como servicio
Seminario: Agentes de IA · Sesión 6 (Despliegue)

Junta TODO el curso en un solo servicio que FastAPI expone:
  ✅ Memoria configurable (buffer o window) — Sesión 3
  ✅ Temperatura configurable                — Sesión 1
  ✅ Herramientas (clima, calculadora, etc.) — Sesión 2-3
  ✅ RAG sobre documentos reales             — Sesión 4
  ✅ Equipo multiagente (investigador, analista, redactor) — Sesión 4
  ✅ Salida estructurada con Pydantic        — Sesión 2
  ✅ Coordinador que decide el camino solo (LangGraph) — Sesión 4

Patrón: Singleton — una sola instancia se crea al arrancar el
servidor y se reutiliza en todas las peticiones.
"""

import os
from dotenv import load_dotenv
from langchain_community.chat_message_histories import ChatMessageHistory

from core.graph import construir_grafo
from core.tools import TOOLS_BASE

load_dotenv()

NOMBRE_AGENTE = os.getenv("AGENT_NAME", "LAUPRÉA BEAUTY")


class AgentService:
    """Servicio que encapsula el grafo del agente completo."""

    def __init__(self):
        self._historiales: dict[str, ChatMessageHistory] = {}
        self._modelo = os.getenv("GROQ_MODEL", os.getenv("OLLAMA_MODEL", "desconocido"))
        self._proveedor = os.getenv("LLM_PROVIDER", "groq")
        # ✏️ MODIFICA AQUÍ: tipo de memoria — "buffer" (recuerda todo)
        # o "window" (solo los últimos N mensajes, ver MEMORY_WINDOW_SIZE)
        self._memory_type = os.getenv("MEMORY_TYPE", "buffer")
        self._window = int(os.getenv("MEMORY_WINDOW_SIZE", "8"))
        self._grafo = construir_grafo()
        print(f"✅ AgentService listo — {self._proveedor}/{self._modelo} · memoria={self._memory_type}")

    def _obtener_historial(self, session_id: str) -> ChatMessageHistory:
        if session_id not in self._historiales:
            self._historiales[session_id] = ChatMessageHistory()
        historial = self._historiales[session_id]
        if self._memory_type == "window" and len(historial.messages) > self._window:
            historial.messages = historial.messages[-self._window:]
        return historial

    def chat(self, mensaje: str, session_id: str = "default") -> dict:
        """
        Procesa un mensaje a través del grafo completo del agente.
        El coordinador decide solo qué camino tomar (conversación,
        documentos/RAG, análisis multiagente o reporte estructurado).
        """
        historial = self._obtener_historial(session_id)

        estado_inicial = {
            "entrada_usuario": mensaje,
            "historial": historial.messages,
            "categoria": "",
            "respuesta_final": "",
            "fuentes": [],
        }

        try:
            resultado = self._grafo.invoke(estado_inicial)
        except Exception as e:
            raise RuntimeError(f"Error en el agente: {e}")

        respuesta = resultado["respuesta_final"]
        historial.add_user_message(mensaje)
        historial.add_ai_message(respuesta)

        return {
            "respuesta": respuesta,
            "categoria": resultado.get("categoria", ""),
            "fuentes": resultado.get("fuentes", []),
        }

    def ejecutar_tarea(self, tarea: str, contexto: str = None, session_id: str = "default") -> dict:
        """Ejecuta una tarea específica con contexto opcional (POST /agent)."""
        entrada = tarea
        if contexto:
            entrada = f"Contexto: {contexto}\n\nTarea: {tarea}"
        return self.chat(entrada, session_id)

    def limpiar_sesion(self, session_id: str) -> bool:
        if session_id in self._historiales:
            del self._historiales[session_id]
            return True
        return False

    @property
    def nombre(self) -> str:
        return NOMBRE_AGENTE

    @property
    def proveedor(self) -> str:
        return self._proveedor

    @property
    def modelo(self) -> str:
        return self._modelo

    @property
    def herramientas(self) -> list:
        return [t.name for t in TOOLS_BASE]


# Instancia global — se crea una sola vez al arrancar el servidor
# ✏️ No modifiques esta línea
agente_service = AgentService()
