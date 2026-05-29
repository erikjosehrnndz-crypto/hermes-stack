---
name: Hermes Website
type: service
status: active
port: 3001
domain: docs.el80.space
port_name: website
docker_network: backend
health_check_endpoint: GET /
last_updated: 2026-05-25
---

# Hermes Website

Frontend de documentación y control del Hermes Stack. Aplicación web Next.js 14 con App Router que renderiza interfaz de usuario, llama a APIs de [[hermes_agent]] y [[litellm_router]], y expone health endpoints.

## Configuración clave

- **Puerto host:** 127.0.0.1:3001
- **Imagen Docker:** website (Next.js 14 standalone)
- **Red Docker:** backend
- **Red externa:** Expuesto vía [[caddy]] en docs.el80.space
- **Framework:** Next.js 14.2.x App Router
- **TypeScript:** Configurado en tsconfig.json
- **CSS:** Tailwind + postcss
- **Directorio:** `website/`

## Relaciones

- Depende de: [[hermes_agent]] (API calls), [[litellm_router]] (indirectamente via [[hermes_agent]])
- Sirve a: [[caddy]]
- Alimenta a: [[prometheus]] (métricas si implementadas)
- Implementa: [[voice_pipeline_e2e]] (frontend de UI)

## Health check

```bash
curl -f http://127.0.0.1:3001/
```

Respuesta: HTML 200

## Configuración Next.js

### Archivo de configuración

```bash
ls -la website/next.config.mjs   # Usar .mjs, NO .ts (Next.js 14)
```

**Crítico:** Next.js 14.x **no** soporta `next.config.ts`. Solo Next.js 15+ lo soporta. Si ves error "Configuring Next.js via 'next.config.ts' is not supported", renombrar a `.mjs`.

### App Router estructura

```
website/
├── app/
│   ├── layout.tsx          # Root layout (metadata, globals.css)
│   ├── page.tsx            # Home page
│   └── api/
│       ├── tree/route.ts   # GET /api/tree
│       └── health/route.ts # GET /health
├── src/
│   ├── App.tsx             # Main component ('use client')
│   ├── index.css           # Tailwind
│   └── components/         # Componentes reutilizables ('use client' si hooks)
├── public/                 # Assets estáticos (debe existir, crear .gitkeep si vacío)
├── tsconfig.json           # TypeScript config
├── postcss.config.js       # PostCSS (requerido por Tailwind)
└── tailwind.config.js      # Tailwind config
```

## Runbook

### Inicio

```bash
docker compose up -d website
```

### Restart

```bash
docker compose restart website
```

### Logs

```bash
docker compose logs -f website
```

### Build local (verificación previa a commit)

```bash
cd website && npm run build
```

**Obligatorio:** Debe completar sin errores TypeScript ni compilación. Nunca commitear con build roto.

### Troubleshooting

| Problema | Síntoma | Solución |
|----------|---------|----------|
| Build falla (TypeScript error) | `error TS...` en npm run build | Revisar tipo de datos, validar 'use client' en componentes con hooks |
| Componente no renderiza | Blanco en navegador, hydration error | Verificar que componente tiene 'use client' si usa useState/useEffect/fetch/window |
| API route no responde | GET /api/tree devuelve 404 | Confirmar archivo existe en `app/api/tree/route.ts`, exporta función GET |
| Docker build falla | "COPY /app/public" error | Crear `website/public/.gitkeep` si `public/` vacío |
| .next no se limpia | Cambios no aparecen después de rebuild | Ejecutar `rm -rf website/.next && docker compose up -d --build website` |

## Métricas

- Latencia de página (First Contentful Paint, Largest Contentful Paint)
- Errores de JavaScript del cliente (si implementado)
- Rate de API calls a [[hermes_agent]]

## Build & Deployment

### Verificar versión instalada

```bash
npm list next
# Debe ser 14.2.x
```

### Config Next.js para Docker standalone

```javascript
// next.config.mjs
export default {
  output: 'standalone', // Requerido para Docker
};
```

### Dockerfile pattern

```dockerfile
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:18-alpine
WORKDIR /app
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/public ./public
EXPOSE 3001
CMD ["node", "server.js"]
```

## Referencias

- Next.js 14 App Router documentation
- [[voice_pipeline_e2e]] — flujo que implementa en frontend
- Dockerfile: `website/Dockerfile`
- CLAUDE.md: sección "Next.js / website"
