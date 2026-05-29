# Reglas — Git

## Push HTTPS — ÚNICO método que funciona en este VPS

El remote usa HTTPS, no SSH. El helper de credenciales git **no está configurado**, por lo que `git push` falla con "could not read Username" si no se incrusta el token. Patrón obligatorio:

```bash
GH_TOKEN=$(gh auth token)
git remote set-url origin "https://erikjosehrnndz-crypto:${GH_TOKEN}@github.com/erikjosehrnndz-crypto/hermes-stack.git"
git push
git remote set-url origin "https://github.com/erikjosehrnndz-crypto/hermes-stack.git"
```

Restaurar la URL limpia después de cada push — el token no debe quedar en el remote URL.

**GitHub username:** `erikjosehrnndz-crypto` (con `-crypto`). No usar versiones sin el sufijo.

## `git add` siempre desde el directorio raíz `/root`

```bash
cd /root && git add <archivo-relativo-al-repo>
# o sin cd:
git -C /root add <archivo>
```

**Previene:** `fatal: pathspec 'X' did not match any files` cuando el shell está en un subdirectorio.

## .gitignore antes de `git add` en cualquier directorio nuevo

Antes de `git add <dir>/`, hacer `ls -la <dir>` e identificar artefactos:

| Directorio | Ignorar |
|---|---|
| `hermes_bp/` | `*.aux *.toc *.out *.lot *.log *.synctex.gz *.db` |
| `website/` | `node_modules/ .next/ dist/ *.db` |
| cualquier Python | `__pycache__/ *.pyc .venv/` |

El `.gitignore` raíz tiene `.*` que ignora todos los dotfiles. Para que los `.gitignore` de subdirectorios funcionen, el raíz tiene `!.gitignore` como excepción. **Consecuencia:** `git add` de cualquier dotfile (`.claude/`, `.env`, etc.) falla.

## Archivos que nunca van al repositorio

```
*.db              # filebrowser.db, ruvector.db — bases de datos runtime
*.zip             # backups y archivos de exportación
Sync/  snap/      # directorios del sistema
*.aux *.toc *.out *.lot *.log   # artefactos LaTeX
node_modules/  .next/  dist/    # dependencias y builds de frontend
.env  .env.*                    # secretos
```

## Verificar build antes de hacer commit (frontend)

```bash
cd website && npm run build   # debe completar sin errores TS ni de compilación
```

Si el build falla, corregir antes de commitear — nunca commitear con el build roto.

## Commit por tarea lógica, no por sesión

Commitear al finalizar cada tarea individual. No acumular cambios de múltiples tareas en un solo commit — si la sesión cae por rate limit, el trabajo sin commit se pierde.

## Commit ANTES de lanzar orquestación multi-agente

`git commit` de todo el trabajo en curso ANTES de lanzar agentes de larga duración. Trabajo no commiteado se puede perder si el context limit ocurre durante la ejecución paralela.

## Nombramiento de ramas

```
feat/<nombre>   fix/<nombre>   docs/<nombre>   chore/<nombre>
```

## Workflow de PR

```bash
git checkout -b feat/mi-feature
# ... trabajo y commits ...
# push usando patrón HTTPS con token (arriba)
gh pr create --title "..." --body "..."
```
