import asyncio
import os
import aiohttp
from aiohttp import web
from prometheus_client import (
    generate_latest,
    CONTENT_TYPE_LATEST,
    Counter,
    Histogram,
    REGISTRY,
)

from core.agent import HermesAgent
from api.health import health_handler

# Metricas de Prometheus para Observabilidad
HTTP_REQUESTS_TOTAL = Counter(
    "hermes_http_requests_total",
    "Total de peticiones HTTP recibidas",
    ["method", "endpoint", "status"],
)
PROCESS_LATENCY = Histogram(
    "hermes_process_latency_seconds", "Latencia del procesamiento de tareas en segundos"
)
ELEVENLABS_STREAM_LATENCY = Histogram(
    "hermes_elevenlabs_stream_latency_seconds",
    "Latencia de la generacion y streaming de voz ElevenLabs",
)


async def metrics_handler(request):
    """Retorna las metricas acumuladas en formato Prometheus."""
    data = generate_latest(REGISTRY)
    ct = CONTENT_TYPE_LATEST.split(";")[0].strip()
    return web.Response(body=data, content_type=ct, charset="utf-8")


async def process_handler(request):
    """Procesa un texto utilizando el agente Hermes y retorna la respuesta sanitizada."""
    try:
        data = await request.json()
        text_input = data.get("text", "").strip()

        if not text_input:
            HTTP_REQUESTS_TOTAL.labels(
                method="POST", endpoint="/process", status="400"
            ).inc()
            return web.json_response(
                {"error": "El parametro 'text' no puede estar vacio."}, status=400
            )

        agent = request.app["agent"]

        with PROCESS_LATENCY.time():
            result = await agent.process_task(text_input)

        HTTP_REQUESTS_TOTAL.labels(
            method="POST", endpoint="/process", status="200"
        ).inc()

        # Fire-and-forget: captura Q&A en Brain (no bloquea la respuesta)
        response_text = result.get("text") or result.get("response") or ""
        if response_text and len(text_input) > 10:
            asyncio.ensure_future(
                _capture_to_brain(request.app, text_input, response_text)
            )

        return web.json_response(result)

    except Exception as e:
        HTTP_REQUESTS_TOTAL.labels(
            method="POST", endpoint="/process", status="500"
        ).inc()
        return web.json_response(
            {"error": f"Fallo al procesar la tarea: {str(e)}"}, status=500
        )


async def _capture_to_brain(app, query: str, response: str) -> None:
    """Fire-and-forget: envía el par Q&A a Brain para memoria conversacional."""
    brain_url = os.getenv("BRAIN_URL", "")
    brain_token = os.getenv("BRAIN_API_TOKEN", "")
    if not brain_url or not brain_token:
        return
    try:
        session = app["agent"]._session
        if session is None or session.closed:
            return
        text = f"Usuario: {query}\nHermes: {response}"
        await session.post(
            f"{brain_url}/api/v1/ingest/text",
            json={
                "text": text,
                "type": "memory",
                "tags": ["hermes", "conversation"],
                "source": "hermes",
            },
            headers={"Authorization": f"Bearer {brain_token}"},
            timeout=aiohttp.ClientTimeout(total=5),
        )
    except Exception:
        pass  # Best-effort, no bloquea


async def on_startup(app):
    await app["agent"].start()


async def on_cleanup(app):
    await app["agent"].stop()


async def init_app():
    """Inicializa la aplicacion web de aiohttp."""
    app = web.Application()

    app["agent"] = HermesAgent()
    app.on_startup.append(on_startup)
    app.on_cleanup.append(on_cleanup)

    app.router.add_get("/health", health_handler)
    app.router.add_get("/metrics", metrics_handler)
    app.router.add_post("/process", process_handler)

    return app


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    print(f"Iniciando Hermes Agent en puerto {port}...")
    web.run_app(init_app(), host="0.0.0.0", port=port)
