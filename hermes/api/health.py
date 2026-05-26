import os
import shutil
import aiohttp
from aiohttp import web


async def health_handler(request):
    agent = request.app["agent"]
    session = agent._session

    litellm_healthy = await check_litellm(agent.litellm_url, session)
    elevenlabs_healthy = await check_elevenlabs(session)
    disk_healthy = check_disk_space()
    skills_healthy = check_critical_skills(agent.skills_dir)

    all_healthy = (
        litellm_healthy and elevenlabs_healthy and disk_healthy and skills_healthy
    )
    status = 200 if all_healthy else 503

    return web.json_response(
        {
            "status": "healthy" if all_healthy else "degraded",
            "checks": {
                "litellm": litellm_healthy,
                "elevenlabs": elevenlabs_healthy,
                "disk": disk_healthy,
                "skills": skills_healthy,
            },
        },
        status=status,
    )


async def check_litellm(
    litellm_url: str, session: aiohttp.ClientSession | None
) -> bool:
    api_key = os.getenv("LITELLM_KEY")
    headers = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    try:
        if session is None or session.closed:
            async with aiohttp.ClientSession() as s:
                async with s.get(
                    f"{litellm_url}/health",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=3),
                ) as resp:
                    return resp.status in (200, 401)
        async with session.get(
            f"{litellm_url}/health",
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=3),
        ) as resp:
            return resp.status in (200, 401)
    except Exception:
        return False


async def check_elevenlabs(session: aiohttp.ClientSession | None) -> bool:
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        return False
    headers = {"xi-api-key": api_key}
    try:
        if session is None or session.closed:
            async with aiohttp.ClientSession() as s:
                async with s.get(
                    "https://api.elevenlabs.io/v1/models",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=4),
                ) as resp:
                    return _elevenlabs_ok(resp.status, None)
        async with session.get(
            "https://api.elevenlabs.io/v1/models",
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=4),
        ) as resp:
            if resp.status == 200:
                return True
            if resp.status == 401:
                data = await resp.json()
                return data.get("detail", {}).get("status") == "missing_permissions"
            return False
    except Exception:
        return False


def _elevenlabs_ok(status: int, _body) -> bool:
    return status == 200


def check_disk_space() -> bool:
    try:
        total, used, free = shutil.disk_usage("/app")
        return (free / total) >= 0.10
    except Exception:
        return False


def check_critical_skills(skills_dir: str) -> bool:
    try:
        return os.path.exists(skills_dir)
    except Exception:
        return False
