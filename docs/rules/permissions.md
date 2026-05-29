# Reglas — Claude Code, configuración de permisos

## Dos archivos, dos roles distintos

| Archivo | Rol |
|---|---|
| `~/.claude/settings.json` | Permisos **canónicos** del proyecto — editar manualmente |
| `~/.claude/settings.local.json` | Acumulación automática de clicks "Allow" — **limpiar periódicamente** |

Toda operación regular del workflow debe estar en `settings.json`, no esperar a que se acumule en `settings.local.json`.

## Permisos canónicos para este VPS

| Patrón | Cubre |
|---|---|
| `Bash(git *)` | git incluyendo push HTTPS con token |
| `Bash(gh *)` | GitHub CLI |
| `Bash(docker *)` | docker compose ps/up/down/logs/inspect |
| `Bash(curl *)` | Health checks post-deploy |
| `Bash(npm *)` | install, run build/dev, list |
| `Bash(xelatex *)` | Compilación LaTeX |
| `Write(/root/website/*)` | Frontend Next.js |
| `Write(/root/hermes/*)` | Código del agente Python |
| `Write(/root/config/*)` | litellm.yaml y configs de servicios |
| `Write(/root/.claude/*)` | Hooks, settings, statusline |
| `Write(/root/docs/*)` | Documentación y reglas modulares |

## `.claude/` está en `.gitignore` — settings.json NO va al repositorio

El `.gitignore` raíz contiene `.*`, que ignora todos los dotfiles incluyendo `.claude/`. `git add .claude/settings.json` falla — vive solo en el VPS. Si el VPS se reinicia o se clona el repo, recrear `settings.json` desde la tabla de arriba.

## Síntoma de acumulación — cuándo limpiar

```bash
cat ~/.claude/settings.local.json | jq '.permissions.allow | length'
```

Si > 20 reglas: revisar si alguna necesita pasar a `settings.json`, luego limpiar:

```bash
echo '{}' > ~/.claude/settings.local.json
```

## Bug — doble slash en Read permissions

`Read(//usr/bin/**)` con doble slash es un bug silencioso — no matchea nada. Verificar tras cualquier consolidación:

```bash
jq '.permissions.allow[]' ~/.claude/settings.json | grep '//'   # debe salir vacío
```
