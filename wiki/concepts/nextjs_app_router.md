---
name: "Next.js App Router"
type: "concept"
category: "pattern"
status: "active"
introduced_date: "2026-05-23"
last_reviewed: "2026-05-25"
---

# Next.js App Router

El frontend del Hermes Stack (`website/`) usa Next.js 14.2.x con App Router. Este concepto documenta las convenciones y restricciones específicas de esta versión que difieren de Next.js 15+.

## Por qué existe

La migración desde React/Vite a Next.js 14 App Router permite usar Server Components, Route Handlers como API endpoints nativos y el modo `output: 'standalone'` para contenedores Docker optimizados. La versión instalada es 14.2.x — anterior a Next.js 15 — lo que impone restricciones específicas que hay que respetar.

## Cómo funciona

### Estructura de archivos

```
website/
├── app/
│   ├── layout.tsx          # Root layout — importa globals CSS, define metadata
│   ├── page.tsx            # Home page — renderiza App component
│   └── api/
│       ├── tree/route.ts   # GET /api/tree — árbol de directorios
│       └── health/route.ts # GET /health   — health check
├── src/
│   ├── App.tsx             # SPA principal ('use client')
│   ├── index.css           # Tailwind + custom styles
│   └── components/         # Componentes React ('use client' si usan hooks)
├── public/                 # Assets estáticos (.gitkeep si está vacío)
├── next.config.mjs         # Configuración Next.js (output: 'standalone')
├── tsconfig.json
├── postcss.config.js
└── tailwind.config.js
```

### Regla crítica: archivo de configuración

Next.js 14.x **no** soporta `next.config.ts`. Solo Next.js 15+ lo soporta.

```
next.config.mjs    ← siempre para Next.js 14
next.config.ts     ← solo Next.js 15+, no usar
```

Error concreto si se usa `.ts` en v14:
```
Error: Configuring Next.js via 'next.config.ts' is not supported.
```

### Directiva `'use client'`

Todo componente que use `useState`, `useEffect`, `fetch`, `window`, `document` u otras APIs de browser debe tener `'use client'` como primera línea (antes de cualquier import):

```tsx
'use client';

import React, { useState, useEffect } from 'react';
```

Sin esta directiva, Next.js intenta renderizarlo en el servidor y lanza errores de hidratación.

### API Routes como Route Handlers

Los endpoints de API se implementan en `app/api/*/route.ts`, no con Express:

```ts
// app/api/ejemplo/route.ts
import { NextResponse } from 'next/server';
export async function GET() {
  return NextResponse.json({ data: 'valor' });
}
```

`next start` sirve tanto el frontend como las API routes — no agregar Express.

### Dockerfile y `public/`

El Dockerfile standalone incluye `COPY --from=builder /app/public ./public`. Si `public/` no existe, el Docker build falla. Crear siempre:

```bash
mkdir -p website/public && touch website/public/.gitkeep
```

### Verificar versión antes de usar features

```bash
npm list next
# o
cat website/node_modules/next/package.json | grep '"version"' | head -1
```

El check de versión debe ser el **primer paso** cuando el plan menciona archivos de configuración version-específicos.

### Build check obligatorio antes de commit

```bash
cd website && npm run build
```

Debe completar sin errores TypeScript ni de compilación. Nunca commitear con el build roto.

## Entidades relacionadas

- [[hermes_website]] — la entidad concreta que implementa este patrón
- [[docker_compose_stack]] — el servicio `website` que corre el contenedor standalone
- [[ci_cd_pipeline]] — el build se verifica en cada deploy
- [[frontend_changes]] — guía operativa para cambios en website/

## Trade-offs

- **Ganado:** SSR/SSG opcional por página, Route Handlers nativos, output standalone para Docker, TypeScript de primera clase.
- **Perdido:** mayor complejidad que React/Vite puro, distinción Server/Client Components requiere atención constante, la versión 14.2.x no soporta `next.config.ts`.

## Evolución

- Migrado desde React/Vite en sesión 2026-05-23.
- El error de `next.config.ts` en v14 fue descubierto durante la migración y documentado.
- La directiva `'use client'` en `App.tsx` fue requerida al migrar componentes con hooks.

## Referencias

- [[frontend_changes]] — workflow completo para cambios en el frontend
- [[adding_new_service]] — si se añade un nuevo servicio que expone frontend
