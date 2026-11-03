"""
============================================================
  routes/agent.py — Endpoint POST /agent
  Seminario: Agentes de IA · Sesión 5

  Para tareas específicas que requieren más contexto
  que una simple conversación.
============================================================
"""

from fastapi import APIRouter, HTTPException
from models.schemas import AgentRequest, AgentResponse, ErrorResponse
from core.agent_core import agente_service

router = APIRouter()


@router.post(
    "/agent",
    response_model=AgentResponse,
    summary="Ejecutar tarea con el agente",
    description="Ejecuta una tarea específica. Permite pasar contexto adicional.",
    responses={500: {"model": ErrorResponse}},
)
async def ejecutar_agente(request: AgentRequest):
    """
    POST /agent

    Body:
        tarea:      Descripción de la tarea a ejecutar
        contexto:   Información adicional (opcional)
        session_id: Identificador de sesión

    Returns:
        AgentResponse con el resultado de la tarea
    """
    try:
        resultado = agente_service.ejecutar_tarea(
            tarea=request.tarea,
            contexto=request.contexto,
            session_id=request.session_id,
        )
        return AgentResponse(
            resultado=resultado["respuesta"],
            tarea=request.tarea,
            session_id=request.session_id,
            categoria=resultado.get("categoria"),
            fuentes=resultado.get("fuentes", []),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ✏️ MODIFICA AQUÍ: agrega endpoints específicos de tu dominio
# Ejemplo para el catálogo de LAUPRÉA:
# @router.post("/agent/stock-bajo")
# async def consultar_stock_bajo():
#     ...
