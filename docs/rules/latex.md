# Reglas — LaTeX / XeLaTeX

## Conflicto Babel español + TikZ — siempre aplicar

Con `\usepackage[spanish]{babel}`, el carácter `>` se vuelve activo y rompe `>=Stealth`. Error: `Package pgfkeys Error: I do not know the key '\par'`.

```latex
\usepackage{tikz}
\usetikzlibrary{babel,arrows.meta,positioning,calc,fit,backgrounds}
%               ^^^^^ babel PRIMERO en la lista, siempre
```

## YAML no existe en listings — definir en preámbulo

`\lstdefinelanguage{yaml}{...}` con `keywords`, `comment=[l]{\#}`, `morestring=[b]'` y `morestring=[b]"`. No está en los paquetes de listings por defecto.

## Fuentes disponibles en este VPS

```
DejaVu Serif / DejaVu Sans / DejaVu Sans Mono  ✓
fontawesome5                                    ✗  (no instalado)
```

No usar `\faIcon{}`. Sustituir con texto o Unicode directo.

## `\checkmark` requiere `amssymb`

```latex
\usepackage{amssymb}   % añadir si se usa \checkmark, \square, \triangleright, etc.
```

Sin el paquete: error `! Undefined control sequence. \checkmark`.

## Compilación — 3 pasadas + verificación

```bash
xelatex -interaction=nonstopmode main.tex   # pasada 1
xelatex -interaction=nonstopmode main.tex   # TOC y labels
xelatex -interaction=nonstopmode main.tex   # outlines e hyperlinks
grep "^!" main.log | sort -u               # debe salir vacío
pdfinfo main.pdf | grep Pages              # verificar página count
```

## Plantilla base del proyecto

`main.tex + s1_*.tex + s2_*.tex + s3_*.tex + s4_*.tex` — compila limpio (24 pp). Usar como plantilla.
