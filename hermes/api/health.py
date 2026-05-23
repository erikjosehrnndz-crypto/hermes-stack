import os
import shutil
import aiohttp
from aiohttp import web

async def health_handler(request):
    """
    Healthcheck que verifica de forma integral la salud del sistema:
    1. Conectividad local con LiteLLM Proxy
    2. Conectividad remota con ElevenLabs API
    3. Espacio libre en disco
    4. Directorio de skills y logs operativos
    """
    agent = request.app["agent"]
    
    litellm_healthy = await check_litellm(agent.litellm_url)
    elevenlabs_healthy = await check_elevenlabs()
    disk_healthy = check_disk_space()
    skills_healthy = check_critical_skills(agent.skills_dir)
    
    all_healthy = litellm_healthy and elevenlabs_healthy and disk_healthy and skills_healthy
    status = 200 if all_healthy else 503
    
    response_data = {
        "status": "healthy" if all_healthy else "degraded",
        "checks": {
            "litellm": litellm_healthy,
            "elevenlabs": elevenlabs_healthy,
            "disk": disk_healthy,
            "skills": skills_healthy
        }
    }
    
    return web.json_response(response_data, status=status)

async def check_litellm(litellm_url: str) -> bool:
    """Verifica que el router LiteLLM este respondiendo."""
    api_key = os.getenv("LITELLM_KEY")
    headers = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{litellm_url}/health", headers=headers, timeout=aiohttp.ClientTimeout(total=3)) as resp:
                return resp.status in (200, 401)
    except Exception:
        return False

async def check_elevenlabs() -> bool:
    """Verifica que la API externa de ElevenLabs sea accesible."""
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        # Si no hay API key configurada todavia, lo marcamos como falso pero no bloquea si estamos en pruebas locales sin llaves
        return False
    try:
        async with aiohttp.ClientSession() as session:
            headers = {"xi-api-key": api_key}
            async with session.get("https://api.elevenlabs.io/v1/models", headers=headers, timeout=aiohttp.ClientTimeout(total=4)) as resp:
                if resp.status == 200:
                    return True
                if resp.status == 401:
                    try:
                        data = await resp.json()
                        status = data.get("detail", {}).get("status")
                        if status == "missing_permissions":
                            return True # La llave es valida pero tiene permisos acotados
                    except Exception:
                        pass
                return False
    except Exception:
        return False

def check_disk_space() -> bool:
    """Verifica que haya suficiente espacio libre en disco (minimo 10%)."""
    try:
        # Leer espacio de la ruta raiz o directorio de trabajo
        total, used, free = shutil.disk_usage("/app")
        pct_free = free / total
        return pct_free >= 0.10
    except Exception:
        return False

def check_critical_skills(skills_dir: str) -> bool:
    """Verifica que el directorio de skills exista y sea accesible."""
    try:
        return os.path.exists(skills_dir)
    except Exception:
        return False
