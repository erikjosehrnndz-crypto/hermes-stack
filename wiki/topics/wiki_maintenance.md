---
name: "Wiki Maintenance"
type: "topic"
difficulty: "beginner"
time_estimate: "30-60 min"
involves: ["agent_orchestration", "ingest_new_source"]
last_updated: "2026-05-25"
---

# Wiki Maintenance

En una línea: procedimiento de lint periódico para detectar y corregir páginas huérfanas, contradicciones, referencias rotas y runbooks obsoletos.

## Por qué importa

Una wiki sin mantenimiento envejece: las referencias rotas crean confusión, los runbooks obsoletos llevan a errores operativos, y las páginas huérfanas no se encuentran nunca. El lint periódico mantiene la wiki navegable y confiable.

## Frecuencia recomendada

- Después de cada ingest significativa (documento nuevo, ADR nuevo, cambio mayor en el stack).
- Semanalmente si hay actividad alta de desarrollo.
- Mensualmente como mínimo.

## Pasos

### 1. Detectar páginas huérfanas

Páginas que no son enlazadas desde ninguna otra:

```bash
# Listar todas las páginas de la wiki
find /root/wiki -name "*.md" | sort

# Para cada página, verificar si algún otro archivo la enlaza
# Formato de link: [[nombre_sin_extension]]
grep -r "\[\[nombre_pagina\]\]" /root/wiki/
```

Las páginas huérfanas deben ser enlazadas desde `_index.md` o desde una página relacionada, o eliminadas si ya no son relevantes.

### 2. Detectar referencias rotas

Links del formato `[[nombre_pagina]]` que apuntan a páginas que no existen:

```bash
# Extraer todos los links de la wiki
grep -roh "\[\[[^]]*\]\]" /root/wiki/ | sort -u

# Verificar que cada [[nombre]] tiene un archivo correspondiente
# (entidades/nombre.md, concepts/nombre.md, topics/nombre.md, sources/nombre.md)
```

Para cada referencia rota: crear la página faltante con contenido mínimo, o corregir el link al nombre correcto.

### 3. Detectar contradicciones

Buscar valores contradictorios (puertos, versiones, rutas) entre páginas:

```bash
# Buscar menciones de un puerto específico
grep -r ":3001" /root/wiki/
grep -r ":4000" /root/wiki/

# Buscar menciones de versiones
grep -r "14.2" /root/wiki/
grep -r "Next.js" /root/wiki/
```

Si dos páginas dicen cosas distintas sobre el mismo hecho, resolver consultando la fuente de verdad (`docker-compose.yml`, `package.json`, `.github/workflows/deploy.yml`) y actualizar la página incorrecta con referencia a la fuente.

### 4. Detectar páginas stale

Páginas con `last_reviewed` más de 3 meses atrás:

```bash
# Buscar fechas de last_reviewed
grep -r "last_reviewed" /root/wiki/ | sort
```

Para cada página stale: verificar que la información sigue siendo correcta contra el estado actual del stack. Actualizar `last_reviewed` si sigue siendo válida.

### 5. Verificar runbooks y comandos

Comandos en `topics/` y `entities/` que referencian deployment o restart:

```bash
grep -r "docker compose" /root/wiki/
grep -r "git push" /root/wiki/
grep -r "curl" /root/wiki/
```

Verificar que los comandos siguen siendo válidos contra:
- `docker-compose.yml` actual (nombres de servicios)
- `.github/workflows/deploy.yml` (pasos del pipeline)
- `.env` (variables referenciadas)

### 6. Detectar hechos sin trazabilidad

Hechos en `entities/` que no tienen link a ninguna `sources/`:

Estos deben marcarse como "local knowledge" añadiendo una nota:
```markdown
<!-- fuente: local knowledge — sin documento de origen -->
```

O añadir la fuente correspondiente si se puede identificar.

### 7. Consolidar si hay duplicación excesiva

Si hay 5+ páginas que hablan del mismo tema (ej. múltiples entidades describiendo el pipeline de voz):
- Crear o actualizar el `concepts/` correspondiente con el tema consolidado.
- Reducir las páginas de entidades a solo config/dependencias específicas.
- Añadir cross-links desde todas las entidades al concepto consolidado.

### 8. Actualizar `_index.md`

Después del lint:
- Añadir páginas nuevas creadas durante el lint.
- Eliminar referencias a páginas que se eliminaron.
- Actualizar estadísticas: total de páginas, fecha de última ingest, páginas stale.

### 9. Commitear los cambios del lint

```bash
git add wiki/
git commit -m "wiki: lint YYYY-MM-DD — descripción de qué se corrigió"
```

## Notas

- **Herramienta para lint automatizado:** si la wiki crece a >100 páginas, considerar un script que automatice los pasos 1-4. Por ahora, el proceso manual es suficiente.
- **No eliminar fuentes:** las páginas en `sources/` son inmutables por diseño. Si una fuente ya no es relevante, marcarla como `status: archived` en el frontmatter, pero no eliminarla.
- **Lint con sub-agentes:** para wikis grandes, el lint puede paralelizarse con agentes Haiku (uno por directorio). Ver [[agent_orchestration]] para el patrón de checkpointing.

## Gotchas

- Corregir una referencia rota creando una página stub vacía es peor que dejar la referencia rota: una página stub puede ser tomada como canónica y propagar información vacía.
- Cambiar el nombre de una página sin actualizar todas sus referencias crea referencias rotas en cadena.
- Las páginas en `sources/` no se editan — si hay un error en una fuente, crear una corrección en la página que la usa, no editar la fuente.

## Véase también

- [[ingest_new_source]] — cómo añadir nueva información de forma estructurada
- [[agent_orchestration]] — paralelizar el lint si la wiki es grande
- `wiki/_index.md` — índice maestro que debe estar siempre actualizado
