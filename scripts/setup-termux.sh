#!/data/data/com.termux/files/usr/bin/bash
# Hermes Stack — Termux Setup (Xiaomi 14T Pro)
# Seguro de re-ejecutar. No modifica lo que ya existe.

set -e

HERMES_IP="100.111.169.105"
HERMES_USER="root"
SSH_KEY="$HOME/.ssh/id_ed25519"

echo "================================================"
echo "  Hermes Stack — Termux Setup"
echo "  VPS: $HERMES_USER@$HERMES_IP (Tailscale)"
echo "================================================"
echo ""

# ── 1. PAQUETES BASE ─────────────────────────────────
echo "[1/8] Instalando paquetes base..."
pkg update -y && pkg upgrade -y
pkg install -y openssh git curl wget python nodejs-lts tmux fzf jq ripgrep make neovim zsh bat btop

# ── 2. CLAUDE CODE ────────────────────────────────────
echo ""
echo "[2/8] Claude Code..."
if ! command -v claude &>/dev/null; then
    npm install -g @anthropic-ai/claude-code
else
    echo "  claude ya instalado: $(claude --version 2>/dev/null || echo 'ok')"
fi

# ── 3. GITHUB CLI ─────────────────────────────────────
echo ""
echo "[3/8] GitHub CLI..."
if ! command -v gh &>/dev/null; then
    pkg install -y gh
else
    echo "  gh ya instalado: $(gh --version | head -1)"
fi

# ── 4. STARSHIP PROMPT ────────────────────────────────
echo ""
echo "[4/8] Starship prompt..."
if ! command -v starship &>/dev/null; then
    curl -sS https://starship.rs/install.sh | sh -s -- --bin-dir "$PREFIX/bin" --yes
else
    echo "  starship ya instalado"
fi

# Activar en .bashrc
if ! grep -q 'starship init bash' "$HOME/.bashrc" 2>/dev/null; then
    echo 'eval "$(starship init bash)"' >> "$HOME/.bashrc"
fi

# Activar en .zshrc
if ! grep -q 'starship init zsh' "$HOME/.zshrc" 2>/dev/null; then
    echo 'eval "$(starship init zsh)"' >> "$HOME/.zshrc"
fi

# ── 5. SSH CONFIG ─────────────────────────────────────
echo ""
echo "[5/8] SSH config..."
mkdir -p "$HOME/.ssh"
chmod 700 "$HOME/.ssh"

# Generar clave si no existe
if [ ! -f "$SSH_KEY" ]; then
    echo "  Generando nueva clave SSH..."
    ssh-keygen -t ed25519 -C "termux@xiaomi-14t-pro" -f "$SSH_KEY" -N ""
    echo ""
    echo "  ┌─────────────────────────────────────────────────────────────┐"
    echo "  │  CLAVE PÚBLICA — añadir al VPS:                             │"
    echo "  │  En el VPS ejecutar:                                        │"
    echo "  │  echo '$(cat "$SSH_KEY.pub")' >> ~/.ssh/authorized_keys     │"
    echo "  └─────────────────────────────────────────────────────────────┘"
else
    echo "  Clave SSH existente: $SSH_KEY"
fi

# Crear/actualizar SSH config
SSH_CONFIG="$HOME/.ssh/config"
if ! grep -q "Host hermes" "$SSH_CONFIG" 2>/dev/null; then
    cat >> "$SSH_CONFIG" << EOF

Host hermes
  HostName $HERMES_IP
  User $HERMES_USER
  IdentityFile $SSH_KEY
  ServerAliveInterval 60
  ServerAliveCountMax 3
  StrictHostKeyChecking no
EOF
    chmod 600 "$SSH_CONFIG"
    echo "  Alias 'hermes' añadido a ~/.ssh/config"
else
    echo "  Alias 'hermes' ya existe en ~/.ssh/config"
fi

# ── 6. TMUX CONFIG ────────────────────────────────────
echo ""
echo "[6/8] tmux config..."
TMUX_CONF="$HOME/.tmux.conf"
if [ ! -f "$TMUX_CONF" ]; then
    cat > "$TMUX_CONF" << 'EOF'
# Hermes — tmux config para Termux
set -g prefix C-a
unbind C-b
bind-key C-a send-prefix
set -g mouse on
set -g history-limit 10000
set -g default-terminal "screen-256color"
set -g status-bg colour235
set -g status-fg white
set -g status-left "[#S] "
set -g status-right "%Y-%m-%d %H:%M"
set -g base-index 1
bind | split-window -h
bind - split-window -v
EOF
    echo "  ~/.tmux.conf creado"
else
    echo "  ~/.tmux.conf ya existe, no modificado"
fi

# ── 7. ALIASES ────────────────────────────────────────
echo ""
echo "[7/8] Aliases..."

add_aliases() {
    local FILE="$1"
    if ! grep -q "# hermes-aliases" "$FILE" 2>/dev/null; then
        cat >> "$FILE" << 'EOF'

# hermes-aliases
alias hermes='ssh hermes'
alias hstatus='ssh hermes make status'
alias hhealth='ssh hermes make health-check'
alias hdoctor='ssh hermes make doctor'
alias hlogs='ssh hermes make logs'
EOF
        echo "  Aliases añadidos a $FILE"
    else
        echo "  Aliases ya existen en $FILE"
    fi
}

add_aliases "$HOME/.bashrc"
[ -f "$HOME/.zshrc" ] || touch "$HOME/.zshrc"
add_aliases "$HOME/.zshrc"

# ── 8. 9ROUTER CONFIG ────────────────────────────────
echo ""
echo "[8/8] 9router (router LLM multi-proveedor)..."

ROUTER_URL="https://router.el80.space/v1"

# Añadir variables de 9router al entorno
if ! grep -q "ANTHROPIC_BASE_URL" "$HOME/.bashrc" 2>/dev/null; then
    cat >> "$HOME/.bashrc" << EOF

# 9router - Router LLM Hermes Stack
export ANTHROPIC_BASE_URL="$ROUTER_URL"
# ANTHROPIC_API_KEY se genera desde: https://router.el80.space/dashboard
# export ANTHROPIC_API_KEY="<pegar_key_android_del_dashboard>"
alias 9rdash='echo "Dashboard: https://router.el80.space/dashboard"'
alias 9rtest='curl -s \$ANTHROPIC_BASE_URL/models -H "Authorization: Bearer \$ANTHROPIC_API_KEY" | python -m json.tool 2>/dev/null | head -20'
EOF
    echo "  Variables 9router añadidas a ~/.bashrc"
else
    echo "  9router ya configurado en ~/.bashrc"
fi

# Misma config en .zshrc
if ! grep -q "ANTHROPIC_BASE_URL" "$HOME/.zshrc" 2>/dev/null; then
    cat >> "$HOME/.zshrc" << EOF

# 9router - Router LLM Hermes Stack
export ANTHROPIC_BASE_URL="$ROUTER_URL"
# export ANTHROPIC_API_KEY="<pegar_key_android_del_dashboard>"
alias 9rdash='echo "Dashboard: https://router.el80.space/dashboard"'
alias 9rtest='curl -s \$ANTHROPIC_BASE_URL/models -H "Authorization: Bearer \$ANTHROPIC_API_KEY" | python -m json.tool 2>/dev/null | head -20'
EOF
fi

# Configurar extra keys de Termux (barra de accesos directos)
TERMUX_PROPS="$HOME/.termux/termux.properties"
mkdir -p "$HOME/.termux"
if ! grep -q "extra-keys" "$TERMUX_PROPS" 2>/dev/null; then
    cat > "$TERMUX_PROPS" << 'EOF'
extra-keys = [['ESC','TAB','CTRL','ALT','|','/','HOME','END'],\
              ['F1','F2','F3','F4','F5','F6','UP','-'],\
              ['9rdash','hstatus','hhealth','LEFT','DOWN','RIGHT','BACKSPACE','DEL']]
EOF
    echo "  Extra keys de Termux configuradas"
    echo "  Reiniciar Termux para aplicar los extra keys"
else
    echo "  Extra keys ya configuradas en $TERMUX_PROPS"
fi

# ── RESUMEN ───────────────────────────────────────────
echo ""
echo "================================================"
echo "  Setup completo"
echo ""
echo "  Conectar al VPS:"
echo "    ssh hermes"
echo ""
echo "  Sesión persistente (recomendado):"
echo "    tmux new -s work && ssh hermes"
echo ""
echo "  Desde dentro del VPS:"
echo "    make status    → ver servicios"
echo "    make doctor    → diagnóstico completo"
echo "    btop           → monitor visual del sistema"
echo ""
echo "  9router (router LLM):"
echo "    Dashboard: https://router.el80.space/dashboard"
echo "    1. Login con la contraseña del VPS"
echo "    2. Endpoints → New → nombre: android"
echo "    3. Copiar key y descomentar ANTHROPIC_API_KEY en ~/.bashrc"
echo ""
echo "  Pendiente:"
echo "    gh auth login  → autenticar GitHub"
echo "    source ~/.bashrc  → activar aliases en esta sesión"
echo "================================================"
