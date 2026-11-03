"""
core/structured.py — Esquemas Pydantic para Salida Estructurada
Seminario: Agentes de IA · Sesión 6 (Despliegue)

Mismo concepto de la Sesión 2 (Structured Output): en vez de dejar
que el modelo redacte libremente, le damos un "formulario" con
casillas fijas que tiene que llenar siempre igual.
"""

from typing import List
from pydantic import BaseModel, Field


class Alerta(BaseModel):
    """Una alerta o riesgo detectado para el reporte ejecutivo."""
    area: str = Field(description="Área afectada: Ventas, Inventario, Marketing, Logística, Servicio al Cliente o Finanzas")
    descripcion: str = Field(description="Descripción concreta del riesgo o alerta")
    accion_recomendada: str = Field(description="Acción concreta recomendada")


class ReporteEjecutivo(BaseModel):
    """Reporte ejecutivo estructurado para LAUPRÉA BEAUTY S.A.S."""
    resumen_ejecutivo: str = Field(description="Resumen del reporte en 2-3 oraciones")
    alertas: List[Alerta] = Field(default_factory=list, description="Alertas o riesgos detectados")
    oportunidades: List[str] = Field(default_factory=list, description="Oportunidades identificadas")
    recomendaciones: List[str] = Field(default_factory=list, description="Recomendaciones priorizadas")
