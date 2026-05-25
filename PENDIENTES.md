# Pendientes — Hermes Stack

---

## 🔴 Crítico

- [ ] **Hermes Agent: 0 requests en 47h** — investigar pipeline de voz (Whisper → `/process`). Verificar que Caddy enruta `hermes.el80.space` correctamente y que el cliente de voz tiene la URL actualizada.

- [ ] **gemini/text-embedding-004 caído en LiteLLM** — verificar que `GEMINI_API_KEY` tiene permiso de embeddings. Probar: `curl -H "Authorization: Bearer $LITELLM_MASTER_KEY" http://127.0.0.1:4000/health`

## 🟡 Advertencia

- [ ] **Añadir litellm a red `monitoring`** en `docker-compose.yml` para que Prometheus pueda scrapearlo y aparezca en Grafana. Actualmente solo está en red `backend`.

- [ ] **Verificar gemini-flash end-to-end** — configurado como modelo por defecto de Hermes pero no aparece en health check de LiteLLM. Probar manualmente:
  ```bash
  source /root/.env
  curl -s -X POST http://127.0.0.1:4000/v1/chat/completions \
    -H "Authorization: Bearer $LITELLM_MASTER_KEY" \
    -H "Content-Type: application/json" \
    -d '{"model":"gemini-flash","messages":[{"role":"user","content":"test"}],"max_tokens":5}' | python3 -m json.tool
  ```

## 🔵 Mejoras

- [ ] Rebuild `hermes` para aplicar cambios de sesión 2026-05-25 (gemini-flash default + health.py session compartida): `docker compose up -d --build hermes`

- [ ] Merge `feat/nextjs-rocket-compat` → `main` para activar el CD pipeline y desplegar todos los cambios acumulados (12 commits adelante de origin)

- [ ] Monitorear latencia E2E en Grafana tras activar gemini-flash como modelo principal

---

*Actualizado: 2026-05-25 · Fuente: `/ruflo-observability:observe-metrics`*
