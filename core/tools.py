"""
core/tools.py — Herramientas del agente
Seminario: Agentes de IA · Sesión 6 (Despliegue)

Reúne las herramientas vistas en el curso:
  - calculadora, fecha_hora_actual, consultar_clima  (Sesión 2-3)
  - buscar_documentos                                (RAG — Sesión 4)
  - analizar_ventas                                  (datos reales en CSV)
"""

import os
import sys
import math
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
import pandas as pd
from langchain_core.tools import tool

from core.rag import obtener_motor


@tool
def calculadora(expresion: str) -> str:
    """Evalúa expresiones matemáticas. Úsala para cualquier cálculo numérico.
    Ejemplos: '2**10', '1024 / 8', 'sqrt(256)'"""
    try:
        ctx = {"sqrt": math.sqrt, "log": math.log, "pi": math.pi,
               "e": math.e, "abs": abs, "round": round,
               "sin": math.sin, "cos": math.cos, "tan": math.tan}
        return f"{expresion} = {eval(expresion, {'__builtins__': {}}, ctx)}"
    except Exception as e:
        return f"Error al calcular: {e}"


@tool
def fecha_hora_actual(zona: str = "America/Bogota") -> str:
    """Devuelve la fecha y hora actual. Úsala cuando pregunten qué hora o qué día es."""
    try:
        now = datetime.now(ZoneInfo(zona))
        return now.strftime(f"%A %d de %B de %Y, %H:%M en {zona}")
    except Exception:
        return datetime.now().strftime("%A %d de %B de %Y, %H:%M")


@tool
def consultar_clima(ciudad: str) -> str:
    """Consulta el clima actual de una ciudad. Úsala para temperatura o condiciones climáticas."""
    key = os.getenv("OPENWEATHER_API_KEY", "")
    if not key or "TU_CLAVE" in key:
        return "La herramienta de clima no está configurada (falta OPENWEATHER_API_KEY)."
    try:
        r = requests.get(
            "https://api.openweathermap.org/data/2.5/weather",
            params={"q": ciudad, "appid": key, "units": "metric", "lang": "es"},
            timeout=10,
        )
        if r.status_code == 404:
            return f"Ciudad '{ciudad}' no encontrada."
        r.raise_for_status()
        d = r.json()
        return (
            f"{d['name']}, {d['sys']['country']}: {d['main']['temp']:.1f}°C, "
            f"{d['weather'][0]['description']}, humedad {d['main']['humidity']}%"
        )
    except Exception as e:
        return f"Error al consultar el clima: {e}"


@tool
def buscar_documentos(pregunta: str) -> str:
    """
    Busca en los documentos internos de LAUPRÉA BEAUTY S.A.S.: política
    comercial, informe del equipo comercial/RRHH, protocolo de atención,
    plan estratégico, catálogo de productos y pedidos recientes. Úsala
    para preguntas sobre precios, tonos, stock, envíos, devoluciones,
    garantías, pedidos o la estrategia de la empresa.
    """
    motor = obtener_motor()
    texto, fuentes = motor.buscar(pregunta)
    if not texto:
        return "No se encontró información relevante en los documentos internos."
    return texto + "\n\nFuentes consultadas: " + ", ".join(fuentes)


@tool
def consultar_catalogo(categoria: str = "", solo_stock_bajo: bool = False) -> str:
    """
    Consulta el catálogo de maquillaje, skincare y accesorios de LAUPRÉA
    BEAUTY: precios, existencias y estado. Úsala cuando pregunten por
    productos, tonos, precios o inventario. Puedes filtrar por categoría
    (Labios, Ojos, Rostro, Skincare, Accesorios) o pedir solo los
    productos con stock bajo.
    """
    ruta = Path(os.getenv("DOCUMENTOS_DIR", "data/documentos")) / "05_catalogo_productos.csv"
    if not ruta.exists():
        return "No se encontró el catálogo de productos."

    df = pd.read_csv(ruta)
    if categoria:
        patron = categoria.strip().lower()
        filtro = (
            df["categoria"].str.lower().str.contains(patron, na=False)
            | df["producto"].str.lower().str.contains(patron, na=False)
        )
        df = df[filtro]
    if solo_stock_bajo:
        df = df[df["stock"] <= df["stock_minimo"]]

    if df.empty:
        return "No se encontraron productos con ese criterio."

    df = df.copy()
    df["precio_cop_fmt"] = df["precio_cop"].map(lambda v: f"${v:,.0f} COP")
    columnas = ["codigo", "producto", "categoria", "precio_cop_fmt", "stock", "estado"]

    # Generar tabla Markdown estructurada con pipes
    header = "| Código | Producto | Categoría | Precio | Stock | Estado |"
    sep    = "| :--- | :--- | :--- | :--- | :--- | :--- |"
    filas  = [
        f"| {r['codigo']} | {r['producto']} | {r['categoria']} | {r['precio_cop_fmt']} | {r['stock']} | {r['estado']} |"
        for _, r in df.iterrows()
    ]
    tabla_md = "\n".join([header, sep] + filas)

    # Gráfica de stock para los primeros productos
    chart_df = df.head(8)
    chart_json = json.dumps({
        "type": "bar",
        "title": f"Stock de Productos ({categoria.capitalize() if categoria else 'Catálogo'})",
        "labels": list(chart_df["producto"]),
        "data": [int(s) for s in chart_df["stock"]]
    }, ensure_ascii=False)

    return f"{tabla_md}\n\n```chart\n{chart_json}\n```"


@tool
def analizar_ventas(agrupar_por: str = "region") -> str:
    """
    Analiza las ventas reales de LAUPRÉA BEAUTY desde el archivo de ventas
    por catálogo. agrupar_por puede ser: 'region', 'producto', 'categoria',
    'canal' o 'mes'. Úsala para preguntas sobre cifras de ventas, qué
    región vende más, productos o categorías más vendidas, canales de
    venta o tendencias por mes.
    """
    ruta = Path(os.getenv("DOCUMENTOS_DIR", "data/documentos")) / "06_ventas_regionales.csv"
    if not ruta.exists():
        return "No se encontró el archivo de ventas."

    df = pd.read_csv(ruta, parse_dates=["fecha"])
    agrupar_por = agrupar_por.strip().lower()

    columnas = {
        "region": "region",
        "producto": "producto",
        "categoria": "categoria",
        "canal": "canal",
        "mes": "mes",
    }
    if agrupar_por not in columnas:
        agrupar_por = "region"

    if agrupar_por == "mes":
        df["mes"] = df["fecha"].dt.strftime("%Y-%m")
        resumen = df.groupby("mes")["valor_total_cop"].sum().sort_index()
    else:
        resumen = df.groupby(columnas[agrupar_por])["valor_total_cop"].sum().sort_values(ascending=False)

    total = float(df["valor_total_cop"].sum())
    unidades = int(df["unidades"].sum())
    
    col_nombre = agrupar_por.capitalize()
    tabla_header = f"| {col_nombre} | Ventas (COP) |\n| :--- | :--- |"
    tabla_filas = [f"| {idx} | ${float(val):,.0f} COP |" for idx, val in resumen.items()]
    tabla_md = tabla_header + "\n" + "\n".join(tabla_filas)

    chart_json = json.dumps({
        "type": "bar",
        "title": f"Ventas por {col_nombre} (COP)",
        "labels": [str(k) for k in resumen.index[:8]],
        "data": [int(v) for v in resumen.values[:8]]
    }, ensure_ascii=False)

    return (
        f"Ventas totales del periodo: ${total:,.0f} COP en {unidades:,.0f} unidades\n\n"
        f"{tabla_md}\n\n"
        f"```chart\n{chart_json}\n```"
    )


# ✏️ MODIFICA AQUÍ: agrega o quita herramientas del agente conversacional
TOOLS_BASE = [
    calculadora,
    fecha_hora_actual,
    consultar_clima,
    buscar_documentos,
    consultar_catalogo,
    analizar_ventas,
]
