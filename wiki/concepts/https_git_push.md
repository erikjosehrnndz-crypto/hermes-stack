---
name: "HTTPS Git Push"
type: "concept"
category: "pattern"
status: "active"
introduced_date: "2026-04-01"
last_reviewed: "2026-05-25"
---

# HTTPS Git Push

El único método de push que funciona en este VPS es HTTPS con token GH incrustado temporalmente en la URL del remote. SSH no está configurado para GitHub en este servidor.

## Por qué existe

El VPS no tiene configurado un helper de credenciales git ni claves SSH registradas en GitHub. El método `git push` por defecto falla con "could not read Username". La solución es incrustar el token de GitHub temporalmente en la URL del remote, hacer el push, y luego restaurar la URL limpia para que el token no quede en la configuración de git.

## Cómo funciona

Patrón obligatorio completo:

```bash
# 1. Obtener token de GitHub CLI
GH_TOKEN=$(gh auth token)

# 2. Incrustar el token en la URL del remote
git remote set-url origin "https://erikjosehrnndz-crypto:${GH_TOKEN}@github.com/erikjosehrnndz-crypto/hermes-stack.git"

# 3. Hacer el push
git push

# 4. Restaurar URL limpia (sin token)
git remote set-url origin "https://github.com/erikjosehrnndz-crypto/hermes-stack.git"
```

### Por qué restaurar la URL limpia

El token no debe quedar en el remote URL porque:
- `git remote -v` lo mostraría en texto plano.
- Si el repositorio se clona o el archivo `.git/config` se lee, el token queda expuesto.
- El token puede aparecer en logs de git o herramientas de IDE.

### GitHub username exacto

El username es `erikjosehrnndz-crypto` — con el sufijo `-crypto`. No usar versiones sin el sufijo. Este username debe coincidir exactamente en la URL del remote.

### Push de rama nueva (primera vez)

```bash
GH_TOKEN=$(gh auth token)
git remote set-url origin "https://erikjosehrnndz-crypto:${GH_TOKEN}@github.com/erikjosehrnndz-crypto/hermes-stack.git"
git push -u origin <nombre-rama>
git remote set-url origin "https://github.com/erikjosehrnndz-crypto/hermes-stack.git"
```

El flag `-u` establece el tracking upstream en el primer push de la rama.

### Workflow completo con PR

```bash
git checkout -b feat/mi-feature
# ... trabajo y commits ...
GH_TOKEN=$(gh auth token)
git remote set-url origin "https://erikjosehrnndz-crypto:${GH_TOKEN}@github.com/erikjosehrnndz-crypto/hermes-stack.git"
git push -u origin feat/mi-feature
git remote set-url origin "https://github.com/erikjosehrnndz-crypto/hermes-stack.git"
gh pr create --title "..." --body "..."
```

## Entidades relacionadas

- [[github_actions]] — el CI/CD que se activa tras el push a `main`
- [[el80_space]] — el VPS donde se ejecutan estos comandos
- [[ci_cd_pipeline]] — el pipeline que se dispara al hacer push a main

## Trade-offs

- **Ganado:** funciona en el VPS sin configuración adicional de SSH o credential helpers.
- **Perdido:** requiere recordar restaurar la URL limpia después de cada push; si se olvida, el token queda expuesto en `.git/config`.

## Evolución

- El patrón se estableció como respuesta al error "could not read Username" en los primeros pushes desde el VPS.
- Se añadió la regla de restaurar URL limpia como medida de seguridad básica.

## Referencias

- [[deployment_workflow]] — el push es parte del workflow de deploy
- [[frontend_changes]] — incluye un push como paso final
