"""
============================================================
  01_verificar_produccion.py — Verifica el deploy en Railway
  Seminario: Agentes de IA · Sesión 6

  Prueba todos los endpoints del agente desplegado
  en Railway desde tu máquina local.

  ✏️ MODIFICA AQUÍ: cambia la URL a la de tu proyecto Railway

  Uso:
      python 01_verificar_produccion.py
============================================================
"""

import requests
import json
import sys

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

# ─────────────────────────────────────────────────────────
#  ✏️ MODIFICA AQUÍ — URL de tu proyecto en Railway
#  Formato: https://tu-proyecto.railway.app
# ─────────────────────────────────────────────────────────
URL_PRODUCCION = "https://TU-PROYECTO.railway.app"

# URL local para comparar
URL_LOCAL = "http://localhost:8000"


def separador(titulo, color=""):
    print(f"\n{'─'*55}")
    print(f"  {titulo}")
    print('─'*55)


def probar_endpoint(base_url, metodo, endpoint, body=None, nombre=""):
    """Prueba un endpoint y devuelve True si funciona."""
    url = f"{base_url}{endpoint}"
    try:
        if metodo == "GET":
            r = requests.get(url, timeout=15)
        elif metodo == "POST":
            r = requests.post(url, json=body, timeout=30)
        elif metodo == "DELETE":
            r = requests.delete(url, timeout=10)

        ok = r.status_code in [200, 201]
        icon = "✅" if ok else "❌"
        print(f"  {icon} {metodo} {endpoint} → {r.status_code}")
        if ok and r.headers.get("content-type", "").startswith("application/json"):
            data = r.json()
            # Muestra solo los campos más relevantes
            if "respuesta" in data:
                print(f"     Respuesta: {data['respuesta'][:80]}...")
            elif "status" in data:
                print(f"     Status: {data['status']}")
            elif "resultado" in data:
                print(f"     Resultado: {data['resultado'][:80]}...")
        return ok
    except requests.ConnectionError:
        print(f"  ❌ {metodo} {endpoint} → Sin conexión")
        return False
    except requests.Timeout:
        print(f"  ⏱️  {metodo} {endpoint} → Timeout (>30s)")
        return False
    except Exception as e:
        print(f"  ❌ {metodo} {endpoint} → Error: {e}")
        return False


def verificar_entorno(base_url, nombre_entorno):
    """Verifica todos los endpoints de un entorno."""
    separador(f"{nombre_entorno}: {base_url}")
    resultados = []

    # Health
    resultados.append(probar_endpoint(base_url, "GET", "/health"))
    resultados.append(probar_endpoint(base_url, "GET", "/health/detail"))
    resultados.append(probar_endpoint(base_url, "GET", "/"))

    # Chat
    resultados.append(probar_endpoint(base_url, "POST", "/chat", {
        # ✏️ MODIFICA AQUÍ: pregunta de prueba según tu dominio
        "mensaje":    "Hola, ¿qué puedes hacer por LAUPRÉA BEAUTY?",
        "session_id": "verificacion_001"
    }))

    # Chat con herramienta
    resultados.append(probar_endpoint(base_url, "POST", "/chat", {
        "mensaje":    "¿Cuánto es 25 elevado a la 2?",
        "session_id": "verificacion_001"
    }))

    # Memoria
    resultados.append(probar_endpoint(base_url, "POST", "/chat", {
        "mensaje":    "¿Cuál fue mi primera pregunta?",
        "session_id": "verificacion_001"
    }))

    # Agent
    resultados.append(probar_endpoint(base_url, "POST", "/agent", {
        # ✏️ MODIFICA AQUÍ: tarea según tu dominio
        "tarea":      "Dame 3 recomendaciones para aumentar las ventas por catálogo",
        "session_id": "verificacion_agente"
    }))

    # Limpiar sesión
    resultados.append(probar_endpoint(base_url, "DELETE", "/chat/verificacion_001"))

    exitosos = sum(resultados)
    total    = len(resultados)
    print(f"\n  Resultado: {exitosos}/{total} endpoints OK")
    return exitosos == total


def main():
    print("\n" + "═"*55)
    print("  Verificación de Despliegue — Sesión 6")
    print("═"*55)

    # Verificar local primero
    local_ok = verificar_entorno(URL_LOCAL, "🖥️  LOCAL")

    # Verificar producción
    if "TU-PROYECTO" in URL_PRODUCCION:
        separador("⚠️  PRODUCCIÓN — No configurada")
        print("  Edita URL_PRODUCCION en este archivo con tu URL de Railway")
        print("  Formato: https://tu-proyecto.railway.app")
    else:
        prod_ok = verificar_entorno(URL_PRODUCCION, "🚀  PRODUCCIÓN (Railway)")

        separador("Resumen final")
        print(f"  Local:      {'✅ OK' if local_ok else '❌ Con errores'}")
        print(f"  Producción: {'✅ OK' if prod_ok else '❌ Con errores'}")

        if prod_ok:
            print(f"\n  🎉 ¡Despliegue exitoso!")
            print(f"  Tu agente está en: {URL_PRODUCCION}")
            print(f"  Documentación:     {URL_PRODUCCION}/docs")

    print("\n" + "═"*55 + "\n")


if __name__ == "__main__":
    main()
