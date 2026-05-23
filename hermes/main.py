import os
from aiohttp import web
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST, Counter, Histogram, REGISTRY
import time

from core.agent import HermesAgent
from api.health import health_handler

# Metricas de Prometheus para Observabilidad
HTTP_REQUESTS_TOTAL = Counter(
    "hermes_http_requests_total", 
    "Total de peticiones HTTP recibidas", 
    ["method", "endpoint", "status"]
)
PROCESS_LATENCY = Histogram(
    "hermes_process_latency_seconds", 
    "Latencia del procesamiento de tareas en segundos"
)
ELEVENLABS_STREAM_LATENCY = Histogram(
    "hermes_elevenlabs_stream_latency_seconds", 
    "Latencia de la generacion y streaming de voz ElevenLabs"
)

async def metrics_handler(request):
    """Retorna las metricas acumuladas en formato Prometheus."""
    data = generate_latest(REGISTRY)
    # aiohttp web.Response content_type cannot contain 'charset'
    ct = CONTENT_TYPE_LATEST.split(";")[0].strip()
    return web.Response(body=data, content_type=ct, charset="utf-8")

# Endpoint para Procesar Tareas de Operacion
async def process_handler(request):
    """Procesa un texto utilizando el agente Hermes y retorna la respuesta sanitizada."""
    status = 200
    start_time = time.time()
    
    try:
        data = await request.json()
        text_input = data.get("text", "").strip()
        
        if not text_input:
            HTTP_REQUESTS_TOTAL.labels(method="POST", endpoint="/process", status="400").inc()
            return web.json_response({"error": "El parametro 'text' no puede estar vacio."}, status=400)

        agent = request.app["agent"]
        
        # Procesamiento bajo medicion de latencia
        with PROCESS_LATENCY.time():
            result = await agent.process_task(text_input)

        HTTP_REQUESTS_TOTAL.labels(method="POST", endpoint="/process", status="200").inc()
        return web.json_response(result)

    except Exception as e:
        status = 500
        HTTP_REQUESTS_TOTAL.labels(method="POST", endpoint="/process", status="500").inc()
        return web.json_response({"error": f"Fallo al procesar la tarea: {str(e)}"}, status=500)

async def init_app():
    """Inicializa la aplicacion web de aiohttp."""
    app = web.Application()
    
    # Instanciamos el Agente en el estado de la aplicacion
    app["agent"] = HermesAgent()
    
    # Registro de rutas
    app.router.add_get("/health", health_handler)
    app.router.add_get("/metrics", metrics_handler)
    app.router.add_post("/process", process_handler)
    
    return app

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    print(f"Iniciando Hermes Agent en puerto {port}...")
    web.run_app(init_app(), host="0.0.0.0", port=port)
