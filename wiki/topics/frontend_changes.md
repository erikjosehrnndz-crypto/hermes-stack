---
name: "Frontend Changes"
type: "topic"
difficulty: "beginner"
time_estimate: "10-30 min"
involves: ["hermes_website", "nextjs_app_router", "docker_compose_stack", "ci_cd_pipeline"]
last_updated: "2026-05-25"
---

# Frontend Changes

En una línea: workflow para hacer cambios en `website/` (Next.js 14.2.x App Router) y llevarlos a producción sin romper el build.

## Por qué importa

El frontend usa Next.js 14.2.x con TypeScript. Los errores de tipado y configuración solo aparecen en build completo, no siempre durante el desarrollo local. Un commit con build roto llega al CI/CD y falla en producción.

## Pasos

### 1. Verificar versión de Next.js antes de usar features nuevas

```bash
npm list next --prefix /root/website
# o
cat /root/website/node_modules/next/package.json | grep '"version"' | head -1
```

Versión instalada: **14.2.x**. Implicaciones:
- Usar `next.config.mjs` — NO `next.config.ts` (solo Next.js 15+)
- Ver [[nextjs_app_router]] para todas las restricciones de versión

### 2. Aplicar la directiva `'use client'` donde corresponde

Cualquier componente que use hooks de React o APIs del browser necesita esta directiva:

```tsx
'use client';   // ← primera línea, antes de imports

import React, { useState, useEffect } from 'react';
```

Aplica a: `src/App.tsx`, cualquier componente en `src/components/` que use `useState`, `useEffect`, `fetch`, `window`, `document`.

### 3. Implementar API endpoints como Route Handlers (no Express)

Los endpoints nuevos van en `app/api/*/route.ts`:

```ts
// app/api/nuevo-endpoint/route.ts
import { NextResponse } from 'next/server';

export async function GET() {
  return NextResponse.json({ data: 'valor' });
}
```

No añadir Express ni otros servidores HTTP — Next.js sirve todo.

### 4. Verificar que `public/` existe

Si es el primer cambio en el directorio `website/` o si `public/` no existe:

```bash
ls /root/website/public/
```

Si no existe o está vacío, crear el placeholder:

```bash
mkdir -p /root/website/public && touch /root/website/public/.gitkeep
```

Sin esto, el Docker build falla en `COPY --from=builder /app/public ./public`.

### 5. Verificar .gitignore antes de `git add`

```bash
ls -la /root/website/
```

Asegurar que estos directorios estén en `.gitignore`:
- `node_modules/`
- `.next/`
- `dist/`
- `*.db`

### 6. Ejecutar el build — obligatorio antes de commitear

```bash
cd /root/website && npm run build
```

El build debe completar sin errores TypeScript ni de compilación. Si falla:
- Revisar errores de tipos TypeScript
- Verificar que todos los componentes con hooks tienen `'use client'`
- Verificar que `next.config.mjs` existe (no `.ts`)

**Nunca commitear con el build roto**, aunque el cambio parezca pequeño.

### 7. Commitear solo los archivos del frontend

```bash
# Solo añadir archivos de website/, no todo el directorio raíz
git add website/src/components/NuevoComponente.tsx
git add website/app/api/nuevo-endpoint/route.ts
# etc.
git commit -m "feat: descripción del cambio en frontend"
```

### 8. Push y verificar CI/CD

Seguir [[deployment_workflow]] para el push y verificación post-deploy.

El contenedor `hermes-website` expone el frontend en `:3001` detrás de Caddy en `docs.el80.space`.

## Notas

- **Tailwind CSS:** requiere `postcss.config.js` + `tailwind.config.js`. Los `content paths` deben incluir `app/` y `src/`.
- **TypeScript:** `tsconfig.json` está configurado para App Router. No cambiar `paths` ni `moduleResolution` sin verificar compatibilidad.
- **output: 'standalone':** el `next.config.mjs` tiene `output: 'standalone'` para el Docker build. No eliminar esta opción.

## Gotchas

- `next.config.ts` en Next.js 14.2.x lanza error inmediato. Siempre `.mjs`.
- Importar un componente Server sin `'use client'` que internamente usa hooks resulta en errores de hidratación crípticos en producción.
- El build local puede pasar pero el Docker build falla si `public/` no existe.

## Véase también

- [[nextjs_app_router]] — concepto completo con todas las reglas de versión
- [[hermes_website]] — entidad del servicio frontend
- [[deployment_workflow]] — pasos completos para deploy
- [[adding_new_service]] — si el cambio introduce un nuevo contenedor
