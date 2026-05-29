#!/usr/bin/env python3
"""Kamatera MCP server — SOLO LECTURA (read-only).

Expone los recursos de una cuenta Kamatera (cloudcli.cloudwm.com) como
herramientas MCP. No incluye ninguna operación de creación, modificación ni
borrado: solo lista/consulta recursos. Credenciales por variables de entorno:

    KAMATERA_API_CLIENT_ID   (AuthClientId)
    KAMATERA_API_SECRET      (AuthSecret)
    KAMATERA_API_URL         (opcional, def. https://cloudcli.cloudwm.com)

Protocolo MCP sobre stdio (JSON-RPC line-delimited). Sin dependencias externas.
"""
import json
import os
import sys
import urllib.request
import urllib.error

API_URL = os.environ.get("KAMATERA_API_URL", "https://cloudcli.cloudwm.com").rstrip("/")
CLIENT_ID = os.environ.get("KAMATERA_API_CLIENT_ID", "")
SECRET = os.environ.get("KAMATERA_API_SECRET", "")
PROTOCOL_VERSION = "2024-11-05"


def api_get(path: str):
    """GET de solo lectura contra la API de Kamatera."""
    url = f"{API_URL}{path}"
    req = urllib.request.Request(url, method="GET")
    req.add_header("AuthClientId", CLIENT_ID)
    req.add_header("AuthSecret", SECRET)
    req.add_header("Accept", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        return {"error": True, "http_status": e.code, "message": e.read().decode("utf-8", "replace")}
    except Exception as e:  # noqa: BLE001
        return {"error": True, "message": str(e)}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"raw": raw}


# --- Definición de herramientas (todas read-only) ---
TOOLS = [
    {
        "name": "kamatera_servers",
        "description": "Lista todos los servidores cloud de la cuenta Kamatera (id, nombre, estado, datacenter, recursos).",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
        "_handler": lambda a: api_get("/service/servers"),
    },
    {
        "name": "kamatera_datacenters",
        "description": "Lista los datacenters disponibles en el catálogo de Kamatera (id, país, ciudad).",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
        "_handler": lambda a: api_get("/service/server?datacenter=1"),
    },
    {
        "name": "kamatera_networks",
        "description": "Lista las redes/VLANs de la cuenta en un datacenter concreto.",
        "inputSchema": {
            "type": "object",
            "properties": {"datacenter": {"type": "string", "description": "ID de datacenter, p.ej. EU-MD"}},
            "required": ["datacenter"],
            "additionalProperties": False,
        },
        "_handler": lambda a: api_get(f"/service/networks?datacenter={a['datacenter']}"),
    },
    {
        "name": "kamatera_images",
        "description": "Lista las imágenes de SO disponibles en un datacenter concreto.",
        "inputSchema": {
            "type": "object",
            "properties": {"datacenter": {"type": "string", "description": "ID de datacenter, p.ej. EU-MD"}},
            "required": ["datacenter"],
            "additionalProperties": False,
        },
        "_handler": lambda a: api_get(f"/service/server?images=1&datacenter={a['datacenter']}"),
    },
    {
        "name": "kamatera_queue",
        "description": "Muestra la cola de tareas/comandos de la cuenta. Opcionalmente el estado de una tarea por id.",
        "inputSchema": {
            "type": "object",
            "properties": {"id": {"type": "string", "description": "ID de tarea (opcional)"}},
            "additionalProperties": False,
        },
        "_handler": lambda a: api_get(f"/service/queue?id={a['id']}" if a.get("id") else "/service/queue"),
    },
]
_HANDLERS = {t["name"]: t["_handler"] for t in TOOLS}
_PUBLIC_TOOLS = [{k: v for k, v in t.items() if not k.startswith("_")} for t in TOOLS]


def handle(msg: dict):
    method = msg.get("method")
    mid = msg.get("id")

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": mid,
            "result": {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "kamatera", "version": "1.0.0"},
            },
        }
    if method in ("notifications/initialized", "initialized"):
        return None  # notificación, sin respuesta
    if method == "ping":
        return {"jsonrpc": "2.0", "id": mid, "result": {}}
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": mid, "result": {"tools": _PUBLIC_TOOLS}}
    if method == "tools/call":
        params = msg.get("params", {})
        name = params.get("name")
        args = params.get("arguments", {}) or {}
        handler = _HANDLERS.get(name)
        if handler is None:
            return {"jsonrpc": "2.0", "id": mid, "error": {"code": -32601, "message": f"Tool desconocida: {name}"}}
        result = handler(args)
        text = json.dumps(result, indent=2, ensure_ascii=False)
        return {"jsonrpc": "2.0", "id": mid, "result": {"content": [{"type": "text", "text": text}]}}

    if mid is not None:
        return {"jsonrpc": "2.0", "id": mid, "error": {"code": -32601, "message": f"Método no soportado: {method}"}}
    return None


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue
        resp = handle(msg)
        if resp is not None:
            sys.stdout.write(json.dumps(resp) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
