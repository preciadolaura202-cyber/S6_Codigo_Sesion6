"""
core/graph.py — Grafo coordinador (LangGraph)
Seminario: Agentes de IA · Sesión 6 (Despliegue)

Este es el "cerebro" que junta TODO lo visto en el curso en un solo
punto de entrada: el COORDINADOR lee la pregunta y decide sola cuál
camino tomar — como en NEXUS.

      START → coordinador → [conversacion | documentos | analisis | reporte] → END

  • conversacion → agente con memoria + herramientas       (Sesiones 1-3)
  • documentos   → RAG sobre los PDFs/CSV internos          (Sesión 4)
  • analisis     → equipo Investigador→Analista→Redactor    (Sesión 4)
  • reporte      → Salida Estructurada con Pydantic         (Sesión 2)

✏️ MODIFICA AQUÍ: ajusta las categorías, los prompts o agrega un
   nuevo camino siguiendo el mismo patrón.
"""

import os
import sys
from typing import TypedDict, Literal

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain.agents import create_agent
from langgraph.graph import StateGraph, START, END

from s6_llm_factory import crear_llm
from core.tools import TOOLS_BASE, buscar_documentos, consultar_catalogo, analizar_ventas
from core.rag import obtener_motor
from core.structured import ReporteEjecutivo

NOMBRE_AGENTE = os.getenv("AGENT_NAME", "LAUPRÉA BEAUTY")
ROL_AGENTE = os.getenv(
    "AGENT_ROLE",
    "Asesora Virtual & Concierge de Belleza de LAUPRÉA BEAUTY S.A.S., experta en cosméticos, skincare y ventas por catálogo",
)


def limpiar_pensamiento(texto: str) -> str:
    """
    Algunos modelos 'razonadores' (ej. qwen3.6) anteponen un bloque
    <think>...</think> con su razonamiento interno antes de la
    respuesta final. Nos quedamos solo con lo que viene después.
    """
    if texto and "</think>" in texto:
        return texto.split("</think>")[-1].strip()
    return (texto or "").strip()


# ═══════════════════════════════════════════════════════════
#  STATE — el diccionario compartido entre todos los nodos
# ═══════════════════════════════════════════════════════════
class EstadoAgente(TypedDict):
    entrada_usuario: str
    historial: list
    categoria: str
    respuesta_final: str
    fuentes: list


# ═══════════════════════════════════════════════════════════
#  COORDINADOR — clasifica y decide el camino (edge condicional)
# ═══════════════════════════════════════════════════════════
def nodo_coordinador(estado: EstadoAgente) -> dict:
    llm = crear_llm(temperature=0.0)
    instrucciones = """Clasifica la pregunta del usuario en UNA categoría:
- conversacion: preguntas sobre la fundadora/creadora (Laura Jimena Quiroz Preciado),
  origen, historia, concepto o visión de LAUPRÉA BEAUTY; saludos, agradecimientos,
  charla sobre maquillaje o belleza en general, tips o rutinas de skincare/maquillaje,
  cálculos matemáticos, hora o clima.
- documentos: preguntas sobre el catálogo de maquillaje, skincare y accesorios
  (precios, tonos, referencias, stock disponible, agotados), políticas de compra,
  políticas de envío, tiempos de entrega, transportadoras, devoluciones, garantías,
  estado de pedidos (guías de rastreo), equipo comercial/RRHH o protocolo de atención.
- reporte: el usuario pide explícitamente un reporte, informe ejecutivo,
  resumen estructurado de dirección, o un "reporte de ventas".
- analisis: el usuario pide analizar, comparar, investigar o evaluar
  a fondo el desempeño de ventas, productos más vendidos, regiones,
  canales de comercialización o tendencias comerciales.

Responde SOLO con la categoría, en minúsculas, sin explicación ni puntuación.

Ejemplos:
"¿Quién creó LAUPRÉA BEAUTY?" -> conversacion
"¿De quién fue la idea de LAUPRÉA BEAUTY?" -> conversacion
"Cuéntame la historia de Laura Quiroz y la marca" -> conversacion
"Hola, ¿cómo estás hoy?" -> conversacion
"¿Qué labial me recomiendas para piel cálida?" -> conversacion
"Dame un tip para que el maquillaje dure más" -> conversacion
"¿Cuánto es 45 * 12?" -> conversacion
"¿Qué hora es en Bogotá?" -> conversacion
"¿Cuánto cuesta el labial Velvet Rose?" -> documentos
"¿Cuál es la política de envíos y devoluciones?" -> documentos
"Muéstrame la tabla de productos y stock" -> documentos
"¿Qué productos tienen stock bajo o están agotados?" -> documentos
"¿Cómo va el pedido PED-2026-1207?" -> documentos
"Genera un reporte ejecutivo de ventas" -> reporte
"Necesito un informe ejecutivo del catálogo" -> reporte
"Dame un resumen estructurado de la situación de LAUPRÉA" -> reporte
"Analiza el desempeño de ventas por región" -> analisis
"Compara las ventas de Bogotá y Medellín y saca conclusiones" -> analisis
"¿Cuáles son los productos más vendidos del mes?" -> analisis
"Investiga qué categoría está creciendo más en ventas" -> analisis
"Hazme un gráfico interactivo de ventas por región" -> analisis
"Muéstrame una gráfica de los productos más vendidos" -> analisis
"Grafica las ventas por canal" -> analisis"""
    resp = llm.invoke([
        SystemMessage(content=instrucciones),
        HumanMessage(content=estado["entrada_usuario"]),
    ])
    contenido = limpiar_pensamiento(resp.content).lower()

    categoria = "conversacion"
    for opcion in ("documentos", "reporte", "analisis", "conversacion"):
        if opcion in contenido:
            categoria = opcion
            break

    print(f"  🎯 [COORDINADOR] → {categoria.upper()}")
    return {"categoria": categoria}


def router(estado: EstadoAgente) -> Literal["conversacion", "documentos", "reporte", "analisis"]:
    return estado.get("categoria", "conversacion")


# ═══════════════════════════════════════════════════════════
#  NODO: CONVERSACIÓN — agente con memoria + herramientas
# ═══════════════════════════════════════════════════════════
def nodo_conversacion(estado: EstadoAgente) -> dict:
    llm = crear_llm()
    system_prompt = f"""Eres {NOMBRE_AGENTE}, la Asesora Oficial de Belleza & Concierge Cosmético de LAUPRÉA BEAUTY S.A.S.
Tu misión es brindar una experiencia glamurosa, cálida, personalizada, empoderadora y sumamente profesional a clientas, asesoras de catálogo y al equipo directivo.

👑 IDENTIDAD Y ORIGEN DE LA MARCA (REGLA FUNDACIONAL DE ORO):
- LAUPRÉA BEAUTY fue concebida y creada por **Laura Jimena Quiroz Preciado**.
- Laura es una talentosa creadora que venía gestando este concepto desde proyectos anteriores, motivada por su deseo de fusionar el desarrollo web frontend y la tecnología interactiva con un diseño visual estético, femenino, sofisticado y funcional.
- Si te preguntan quién creó LAUPRÉA BEAUTY, quién tuvo la idea, sobre la historia de la marca o sobre Laura Quiroz, responde SIEMPRE con orgullo, elegancia y entusiasmo, resaltando esta visión de unir tecnología, estética visual y empoderamiento a través de la cosmética.

💄 ESTILO Y TONO DE COMUNICACIÓN:
- Tono: Sofisticado, cálido, chic, empático, entusiasta y muy profesional.
- Saludo: Acogedor, distinguido y cercano.
- Emojis con buen gusto y estilo: 💄, ✨, 🌸, 💋, 🧴, 💅, 💎, 🛍️.
- Formato impecable en Markdown: utiliza negritas para nombres de productos y precios (`$XX.XXX COP`), viñetas ordenadas y listas atractivas.
- Asesoría experta: Cuando soliciten consejos de maquillaje o cuidado de la piel, ofrece tips profesionales, combinaciones de tonos y rutinas paso a paso recomendando los productos icónicos de LAUPRÉA BEAUTY (ej. Labial Velvet Rose, Base Líquida Skin Glow, Paleta Sunset 12 Tonos, Crema Hidratante Aqua Balance).
- Clima y belleza: Si consultan el clima, además del dato meteorológico exacto, brinda un breve consejo de belleza o skincare adaptado a ese clima (ej. hidratación profunda para climas fríos o protección solar y base ligera para climas cálidos).

🛠️ USO DE HERRAMIENTAS:
- Nunca inventes datos numéricos, precios, existencias ni políticas:
  * Usa 'consultar_catalogo' cuando pregunten por productos, tonos o existencias.
  * Usa 'buscar_documentos' para políticas de envío, devoluciones, garantías o pedidos.
  * Usa 'analizar_ventas' para cifras y tendencias comerciales.
  * Usa 'calculadora', 'fecha_hora_actual' o 'consultar_clima' según aplique."""
    
    agente = create_agent(model=llm, tools=TOOLS_BASE, system_prompt=system_prompt)
    resultado = agente.invoke({
        "messages": estado["historial"] + [HumanMessage(content=estado["entrada_usuario"])]
    })
    return {"respuesta_final": limpiar_pensamiento(resultado["messages"][-1].content)}


# ═══════════════════════════════════════════════════════════
#  NODO: DOCUMENTOS — RAG sobre los PDFs/CSV internos
# ═══════════════════════════════════════════════════════════
def nodo_documentos(estado: EstadoAgente) -> dict:
    motor = obtener_motor()
    contexto, fuentes = motor.buscar(estado["entrada_usuario"])
    catalogo_actual = consultar_catalogo.invoke({"categoria": "", "solo_stock_bajo": False})
    fuentes = sorted(set(fuentes + ["05_catalogo_productos.csv"]))

    llm = crear_llm(temperature=0.2)
    prompt = ChatPromptTemplate.from_messages([
        ("system", f"""Eres {NOMBRE_AGENTE}, Asesora Oficial de Catálogo y Especialista de LAUPRÉA BEAUTY S.A.S.
Responde de forma clara, cálida, glamurosa y con precisión absoluta basándote ÚNICAMENTE en el contexto de los documentos internos y en el catálogo actual proporcionado.

REGLAS DE ESTILO Y PRESENTACIÓN:
1. Formato estructurado y estético en Markdown:
   - Resalta siempre los nombres de productos en negrita (**Producto**).
   - Precios siempre formateados en pesos colombianos con separador de miles (ej. `$42.900 COP`).
   - Muestra el código de referencia cuando aplique (ej. `LB-001`).
   - Muestra el estado de disponibilidad con elegancia visual:
     * `✅ Disponible (X unidades)`
     * `⚠️ Pocas unidades en stock (X unidades restantes)`
     * `❌ Agotado temporalmente`
   - Si el usuario solicita ver el catálogo, inventario o una lista comparativa, preséntalo en una tabla Markdown limpia (`| Código | Producto | Categoría | Precio (COP) | Stock | Estado |`).
2. Políticas y pedidos:
   - Explica las políticas de envíos (tiempos de entrega, transportadoras como Servientrega, Envía, Coordinadora o Interrapidísimo), devoluciones (plazos, condiciones de higiene) y pedidos con total claridad, empatía y profesionalismo.
3. Precisión:
   - Si la información solicitada no figura en el contexto ni en el catálogo, explícalo con amabilidad sin inventar datos.
   - Cita brevemente las fuentes consultadas al final con elegancia."""),
        ("human", "Contexto de los documentos internos:\n{contexto}\n\n"
                  "Catálogo actual (precios y stock):\n{catalogo}\n\n"
                  "Pregunta del usuario: {pregunta}"),
    ])
    chain = prompt | llm | StrOutputParser()
    respuesta = chain.invoke({
        "contexto": contexto or "(no se encontró contexto relevante)",
        "catalogo": catalogo_actual,
        "pregunta": estado["entrada_usuario"],
    })
    return {"respuesta_final": limpiar_pensamiento(respuesta), "fuentes": fuentes}


# ═══════════════════════════════════════════════════════════
#  NODO: ANÁLISIS — equipo Investigador → Analista → Redactor
# ═══════════════════════════════════════════════════════════
def nodo_analisis(estado: EstadoAgente) -> dict:
    print("  🔍 [INVESTIGADOR] Recopilando información...")
    agente_investigador = create_agent(
        model=crear_llm(temperature=0.3),
        tools=[buscar_documentos, consultar_catalogo, analizar_ventas],
        system_prompt="""Eres el Investigador de Negocios de LAUPRÉA BEAUTY S.A.S.
Usa tus herramientas para recopilar datos reales, cifras exactas en pesos colombianos (COP), unidades vendidas, catálogo, stock y políticas antes de emitir conclusiones.
Sé riguroso, cuantitativo y preciso. Responde en español en una lista de puntos clave estructurada.""",
    )
    investigacion = limpiar_pensamiento(agente_investigador.invoke({
        "messages": [HumanMessage(content=f"Investiga sobre: {estado['entrada_usuario']}")]
    })["messages"][-1].content)

    print("  📊 [ANALISTA] Analizando información...")
    analisis = limpiar_pensamiento(crear_llm(temperature=0.4).invoke([
        SystemMessage(content="""Eres la Analista Estratégica Senior de LAUPRÉA BEAUTY S.A.S.
Examina los datos recopilados: identifica categorías líderes, desempeño por regiones (Bogotá, Medellín, Cali, etc.), canales de comercialización (Asesoras, WhatsApp, Catálogo digital) y riesgos u oportunidades de stock.
Prioriza los hallazgos con visión ejecutiva. Responde en español estructurado."""),
        HumanMessage(content=f"Pregunta: {estado['entrada_usuario']}\n\n"
                              f"Información recopilada:\n{investigacion}\n\nAnaliza y concluye con visión de negocio."),
    ]).content)

    print("  ✍️  [REDACTOR] Redactando respuesta final...")
    redaccion = limpiar_pensamiento(crear_llm(temperature=0.5).invoke([
        SystemMessage(content=f"""Eres {NOMBRE_AGENTE}, Directora de Experiencia y Asesora Senior de LAUPRÉA BEAUTY.
Toma el análisis recibido y transfórmalo en una entrega final cautivadora, sumamente profesional y estéticamente organizada para la clienta o el equipo directivo.

Estructura tu respuesta en Markdown con:
- 💎 **Diagnóstico & Panorama General**
- 📈 **Rendimiento Comercial & Cifras Clave** (destacando valores en COP y unidades)
- ⚠️ **Puntos Críticos & Alertas de Inventario**
- 🚀 **Estrategia & Recomendaciones Accionables**

REGLA ESPECIAL PARA GRÁFICAS INTERACTIVAS Y ANIMADAS:
- Si el usuario solicitó un gráfico, gráfica, visualización o si el análisis compara datos clave de regiones, categorías o canales, incluye SIEMPRE al inicio de tu respuesta un bloque de código ```chart con formato JSON válido para que el frontend dibuje el gráfico animado e interactivo con movimiento:
```chart
{
  "type": "bar",
  "title": "Ventas por Región (COP)",
  "labels": ["Bogotá", "Medellín", "Cali", "Barranquilla"],
  "data": [95000000, 72000000, 48000000, 31000000]
}
```
Tipos de gráfico admitidos: "bar", "doughnut" o "line". El campo "data" debe contener sólo números sin formato de texto.

Usa un tono empoderador, sofisticado, cálido y elegante. Responde en español."""),
        HumanMessage(content=f"Pregunta original: {estado['entrada_usuario']}\n\n"
                              f"Análisis:\n{analisis}\n\nRedacta la respuesta final."),
    ]).content)

    return {"respuesta_final": redaccion}


# ═══════════════════════════════════════════════════════════
#  NODO: REPORTE — Salida Estructurada con Pydantic
# ═══════════════════════════════════════════════════════════
def nodo_reporte(estado: EstadoAgente) -> dict:
    modelo_estructurado = os.getenv("GROQ_MODEL_ESTRUCTURADO", "openai/gpt-oss-120b")
    llm_estructurado = crear_llm(temperature=0.4, modelo=modelo_estructurado).with_structured_output(ReporteEjecutivo)
    datos_categoria = analizar_ventas.invoke({"agrupar_por": "categoria"})
    datos_region = analizar_ventas.invoke({"agrupar_por": "region"})
    datos_stock = consultar_catalogo.invoke({"categoria": "", "solo_stock_bajo": True})
    datos = (
        f"VENTAS POR CATEGORÍA\n{datos_categoria}\n\n"
        f"VENTAS POR REGIÓN\n{datos_region}\n\n"
        f"PRODUCTOS CON STOCK BAJO O AGOTADO\n{datos_stock}"
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", """Genera un reporte ejecutivo de alta dirección para LAUPRÉA BEAUTY S.A.S.,
marca de cosméticos, skincare y accesorios de belleza por catálogo.
Basa el reporte estrictamente en los datos provistos.
Sé estratégico, claro, cuantitativo y accionable. Responde en español."""),
        ("human", "Solicitud: {solicitud}\n\nDatos disponibles:\n{datos}"),
    ])
    chain = prompt | llm_estructurado
    reporte: ReporteEjecutivo = chain.invoke({
        "solicitud": estado["entrada_usuario"],
        "datos": datos,
    })

    salida = (
        "## 📋 REPORTE EJECUTIVO DE DIRECCIÓN — LAUPRÉA BEAUTY S.A.S.\n"
        "### *Inteligencia Comercial & Gestión de Catálogo*\n\n"
        f"> 📌 **Resumen Ejecutivo:**\n> {reporte.resumen_ejecutivo}\n\n"
    )
    if reporte.alertas:
        salida += "### 🚨 Alertas & Riesgos Prioritarios\n\n"
        for a in reporte.alertas:
            salida += f"- **[{a.area}]** {a.descripcion}\n  *Acción recomendada:* {a.accion_recomendada}\n\n"
    if reporte.oportunidades:
        salida += "### ✨ Oportunidades Comerciales de Crecimiento\n\n"
        salida += "\n".join(f"- {o}" for o in reporte.oportunidades) + "\n\n"
    if reporte.recomendaciones:
        salida += "### 🎯 Recomendaciones Estratégicas Accionables\n\n"
        salida += "\n".join(f"- {r}" for r in reporte.recomendaciones)

    return {"respuesta_final": salida}


# ═══════════════════════════════════════════════════════════
#  CONSTRUCCIÓN DEL GRAFO
# ═══════════════════════════════════════════════════════════
def construir_grafo():
    grafo = StateGraph(EstadoAgente)

    grafo.add_node("coordinador", nodo_coordinador)
    grafo.add_node("conversacion", nodo_conversacion)
    grafo.add_node("documentos", nodo_documentos)
    grafo.add_node("analisis", nodo_analisis)
    grafo.add_node("reporte", nodo_reporte)

    grafo.add_edge(START, "coordinador")
    grafo.add_conditional_edges("coordinador", router, {
        "conversacion": "conversacion",
        "documentos": "documentos",
        "analisis": "analisis",
        "reporte": "reporte",
    })
    grafo.add_edge("conversacion", END)
    grafo.add_edge("documentos", END)
    grafo.add_edge("analisis", END)
    grafo.add_edge("reporte", END)

    return grafo.compile()
