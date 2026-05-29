# Kamatera MCP — solo lectura

Servidor MCP que expone los recursos de la cuenta Kamatera (`cloudcli.cloudwm.com`)
para **consultarlos** desde Claude Code. **No** crea, modifica ni borra nada en Kamatera.

## Herramientas

| Tool | Qué hace |
|---|---|
| `kamatera_servers` | Lista los servidores cloud de la cuenta |
| `kamatera_datacenters` | Lista los 26 datacenters del catálogo |
| `kamatera_networks` | Redes/VLANs de la cuenta en un datacenter (`datacenter`) |
| `kamatera_images` | Imágenes de SO disponibles en un datacenter (`datacenter`) |
| `kamatera_queue` | Cola de tareas; estado de una tarea con `id` |

## Credenciales

No están en el código. Se guardan en la config del MCP (`~/.claude.json`, fuera del repo)
como variables de entorno `KAMATERA_API_CLIENT_ID` y `KAMATERA_API_SECRET`.

Rotar / reconfigurar:

```bash
claude mcp remove kamatera -s user
claude mcp add kamatera -s user \
  -e KAMATERA_API_CLIENT_ID=<nuevo_client_id> \
  -e KAMATERA_API_SECRET=<nuevo_secret> \
  -- python3 /root/integrations/kamatera/kamatera_mcp.py
```

Las claves se obtienen en https://console.kamatera.com/keys
