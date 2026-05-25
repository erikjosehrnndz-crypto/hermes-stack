# Pendientes — Hermes Stack

Estado formal en `PENDIENTES.json`. Esta tabla es la vista rápida.

| ID | Servicio | Prioridad | Estado | Próximo paso |
|---|---|---|---|---|
| hs-001 | hermes-agent | 🔴 crítico | not-started | Revisar logs Whisper→/process |
| hs-002 | litellm-router | 🔴 crítico | not-started | Verificar GEMINI_API_KEY permisos |
| hs-003 | infra | 🟡 warning | not-started | Añadir litellm a red monitoring |
| hs-004 | litellm-router | 🟡 warning | not-started | Test gemini-flash E2E |
| hs-005 | hermes-agent | 🔵 mejora | not-started | `docker compose up -d --build hermes` |
| hs-006 | infra | 🔵 mejora | not-started | Merge feat/nextjs-rocket-compat → main |

Ver estado detallado y comandos de verificación en `PENDIENTES.json`.

---

## 🔴 Crítico

**hs-001 — Hermes Agent: 0 requests en 47h**
- Investigar pipeline de voz (Whisper → `/process`). Verificar que Caddy enruta `hermes.el80.space` correctamente y que el cliente de voz tiene la URL actualizada.
- **Verificación:** `curl -f http://127.0.0.1:8080/health && docker compose logs hermes --tail=20 | grep 'POST /process'`
- **Evidencia:** _pendiente_

**hs-002 — gemini/text-embedding-004 caído en LiteLLM**
- Verificar que `GEMINI_API_KEY` tiene permiso de embeddings.
- **Verificación:** `source /root/.env && curl -H "Authorization: Bearer $LITELLM_MASTER_KEY" http://127.0.0.1:4000/health`
- **Evidencia:** _pendiente_

## 🟡 Advertencia

**hs-003 — Añadir litellm a red `monitoring`** en `docker-compose.yml` para que Prometheus pueda scrapearlo y aparezca en Grafana.
- **Verificación:** `docker compose ps litellm | grep monitoring`
- **Evidencia:** _pendiente_

**hs-004 — Verificar gemini-flash end-to-end**
- Configurado como modelo por defecto de Hermes pero no aparece en health check de LiteLLM.
- **Verificación:**
  ```bash
  source /root/.env
  curl -s -X POST http://127.0.0.1:4000/v1/chat/completions \
    -H "Authorization: Bearer $LITELLM_MASTER_KEY" \
    -H "Content-Type: application/json" \
    -d '{"model":"gemini-flash","messages":[{"role":"user","content":"test"}],"max_tokens":5}' | python3 -m json.tool
  ```
- **Evidencia:** _pendiente_

## 🔵 Mejoras

**hs-005 — Rebuild `hermes`** para aplicar cambios de sesión 2026-05-25 (gemini-flash default + health.py session compartida):
```bash
docker compose up -d --build hermes
```
- **Verificación:** `docker compose ps hermes | grep Up`
- **Evidencia:** _pendiente_

**hs-006 — Merge `feat/nextjs-rocket-compat` → `main`** para activar el CD pipeline y desplegar todos los cambios acumulados (12 commits adelante de origin)
- **Verificación:** `git log --oneline main..HEAD | wc -l  # debe ser 0`
- **Evidencia:** _pendiente_

---

*Actualizado: 2026-05-25 · Estado formal: `/root/PENDIENTES.json`*
