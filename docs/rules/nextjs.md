# Reglas — Next.js / website

La carpeta `website/` usa **Next.js 14 App Router + TypeScript**. Versión instalada: 14.2.x.

## Archivo de configuración — `.mjs`, nunca `.ts`

Next.js 14.x **no** soporta `next.config.ts` (solo 15+).

```
✓  next.config.mjs    ← usar siempre para Next.js 14
✗  next.config.ts     ← Error: Configuring Next.js via 'next.config.ts' is not supported.
```

## App Router — `'use client'` en componentes con hooks

Todo componente que use `useState`, `useEffect`, `fetch`, `window`, `document` u otras APIs de browser **debe** tener `'use client'` como primera línea (antes de cualquier import):

```tsx
'use client';
import React, { useState, useEffect } from 'react';
```

Aplica a `src/App.tsx` y cualquier componente en `src/components/` que use hooks. Sin la directiva → errores de hidratación o módulos de browser no disponibles.

## Dockerfile standalone — `public/` debe existir

El Dockerfile incluye `COPY --from=builder /app/public ./public`. Si `public/` no existe, el build falla. Crear siempre:

```bash
mkdir -p website/public && touch website/public/.gitkeep
git add website/public/.gitkeep
```

## Estructura de archivos App Router

```
website/
├── app/
│   ├── layout.tsx          # Root layout — globals CSS, metadata
│   ├── page.tsx            # Home — renderiza App
│   └── api/
│       ├── tree/route.ts   # GET /api/tree
│       └── health/route.ts # GET /health
├── src/
│   ├── App.tsx             # SPA principal ('use client')
│   ├── index.css           # Tailwind + custom
│   └── components/         # 'use client' si usan hooks
├── public/                 # .gitkeep si vacío
├── next.config.mjs         # output: 'standalone'
├── tsconfig.json
├── postcss.config.js       # requerido por Tailwind
└── tailwind.config.js      # content paths: app/ y src/
```

## API Routes — Route Handlers, no Express

```ts
// app/api/ejemplo/route.ts
import { NextResponse } from 'next/server';
export async function GET() {
  return NextResponse.json({ data: 'valor' });
}
```

No añadir Express — `next start` sirve frontend y API routes.

## `force-dynamic` obligatorio en routes GET con datos en tiempo real

Next.js 14 cachea rutas `GET` por defecto en production build. Añadir **como primera exportación**:

```ts
export const dynamic = 'force-dynamic';
```

Build confirma: con directiva `ƒ (Dynamic)`, sin ella `○ (Static)`. Previene health check always-healthy y métricas congeladas.

## `.next/` — artefacto de build, nunca al repositorio

Está en `.gitignore` raíz. Confirmar que esté ignorado antes de `git add` en `website/`.

## API Routes con fetch interno a Docker

Las rutas server-side corren dentro del contenedor `hermes-website` (red `backend`). Acceden a otros servicios por hostname de Docker:

```typescript
const HERMES = process.env.HERMES_URL_INTERNAL ?? 'http://hermes:8080';
const LITELLM = process.env.LITELLM_URL_INTERNAL ?? 'http://litellm:4000';
```

### AbortSignal.timeout() — timeout en fetch

```typescript
const res = await fetch(url, { signal: AbortSignal.timeout(3000) });
```

No usar `new AbortController()` + `setTimeout` — `AbortSignal.timeout` es más limpio (Node 17+).

### LiteLLM desde la UI — 401 = servicio up

```typescript
litellmUp = [200, 401].includes(litellmRes.value.status);
```

LiteLLM responde 401 sin auth válida, pero confirma que está corriendo.

### LiteLLM — Prometheus y modelos caídos en silencio

`callbacks: ["prometheus"]` en `litellm_settings`. Endpoint `/metrics/` (trailing slash) → `metrics_path: '/metrics/'` en prometheus.yml.

Si un modelo aparece en litellm.yaml pero no en `GET /v1/models`: LiteLLM lo deshabilitó tras fallo de API. Testear directo al proveedor — `RESOURCE_EXHAUSTED` = cuota agotada → redirigir por OpenRouter (`openrouter/<provider>/<model>`).
