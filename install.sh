#!/usr/bin/env bash
set -euo pipefail

# clap — Claude Code Profile Manager installer
# macOS / Linux compatible one-click install

# ── Colors (auto-detect TTY) ──────────────────────────────────────────
if [ -t 1 ]; then
  BOLD='\033[1m';    DIM='\033[2m'
  GREEN='\033[0;32m'; YELLOW='\033[0;33m'; RED='\033[0;31m'
  CYAN='\033[0;36m';  NC='\033[0m'
else
  BOLD=''; DIM=''; GREEN=''; YELLOW=''; RED=''; CYAN=''; NC=''
fi

log()    { printf "${DIM}[clap]${NC} %s\n" "$*"; }
ok()     { printf "${GREEN}${BOLD}[clap]${NC} ${GREEN}✔ %s${NC}\n" "$*"; }
warn()   { printf "${YELLOW}${BOLD}[clap]${NC} ${YELLOW}⚠ %s${NC}\n" "$*" >&2; }
err()    { printf "${RED}${BOLD}[clap]${NC} ${RED}✘ %s${NC}\n" "$*" >&2; exit 1; }

# ── Detect OS ─────────────────────────────────────────────────────────
OS="$(uname -s)"
case "$OS" in
  Darwin)  OS_NAME="macOS"   ;;
  Linux)   OS_NAME="Linux"   ;;
  *)       err "Unsupported OS: $OS" ;;
esac

# ── Check Python 3 ────────────────────────────────────────────────────
PYTHON=""
for candidate in python3 python python3.13 python3.12 python3.11 python3.10 python3.9 python3.8; do
  if command -v "$candidate" >/dev/null 2>&1; then
    ver=$("$candidate" -c 'import sys; print(sys.version_info[:2])' 2>/dev/null || true)
    if [ "${ver:1:1}" -ge 3 ] 2>/dev/null; then
      PYTHON="$candidate"
      PY_VER=$("$candidate" --version 2>&1)
      break
    fi
  fi
done

if [ -z "$PYTHON" ]; then
  err "Python 3.8+ required but not found. Install it first:
    macOS:  brew install python3
    Linux:  sudo apt install python3  (or equivalent)"
fi
log "Found ${PYTHON} → ${PY_VER}"

# ── Determine install directory ───────────────────────────────────────
INSTALL_DIR=""
for dir in "$HOME/.local/bin" "$HOME/bin" "/usr/local/bin"; do
  if [ -d "$dir" ]; then
    INSTALL_DIR="$dir"
    break
  fi
done

if [ -z "$INSTALL_DIR" ]; then
  INSTALL_DIR="$HOME/.local/bin"
  mkdir -p "$INSTALL_DIR"
  log "Created ${INSTALL_DIR}"
fi

# Check if install_dir is in PATH
in_path() {
  case ":$PATH:" in
    *:"$1":*) return 0 ;;
    *)        return 1 ;;
  esac
}

if ! in_path "$INSTALL_DIR"; then
  warn "${INSTALL_DIR} is not in your PATH"
  SHELL_NAME="$(basename "${SHELL:-$SHELL}")"
  case "$SHELL_NAME" in
    zsh)  RC="$HOME/.zshrc"  ;;
    bash) RC="$HOME/.bashrc" ;;
    fish) RC="$HOME/.config/fish/config.fish" ;;
    *)    RC="$HOME/.profile" ;;
  esac
  warn "Add this to your ${RC}:"
  printf "  ${BOLD}export PATH=\"%s:\$PATH\"${NC}\n" "$INSTALL_DIR"
else
  log "Install dir ${INSTALL_DIR} is in PATH"
fi

# ── Migrate old ~/.claude-switcher → ~/.clap (if present) ────────────
OLD_DIR="$HOME/.claude-switcher"
NEW_DIR="$HOME/.clap"

if [ -d "$OLD_DIR" ] && [ ! -d "$NEW_DIR/presets" ]; then
  log "Migrating old data from ${OLD_DIR} → ${NEW_DIR}"
  mkdir -p "$NEW_DIR"
  for sub in presets backups; do
    if [ -d "$OLD_DIR/$sub" ]; then
      cp -r "$OLD_DIR/$sub" "$NEW_DIR/$sub" 2>/dev/null || true
      ok "Migrated ~/.claude-switcher/${sub}"
    fi
  done
  if [ -f "$OLD_DIR/active" ]; then
    cp "$OLD_DIR/active" "$NEW_DIR/active" 2>/dev/null || true
  fi
fi

# ── Create runtime directories ────────────────────────────────────────
mkdir -p "$NEW_DIR/presets" "$NEW_DIR/backups"
chmod 700 "$NEW_DIR"
log "Runtime dirs ready at ${NEW_DIR}"

# ── Install ───────────────────────────────────────────────────────────
TARGET="$INSTALL_DIR/clap"

# Detect if we're piped (curl | bash) or running from a local clone
if [ -f "$(dirname "$0")/clap.py" ] && [ "$(basename "$0")" != "bash" ]; then
  # Running from local repo
  SOURCE="$(cd "$(dirname "$0")" && pwd)/clap.py"
else
  # Piped or remote — download clap.py from GitHub
  SOURCE="$(mktemp /tmp/clap.py.XXXXXX)"
  REPO="pterchan/clap"
  BRANCH="main"
  GITHUB_URL="https://raw.githubusercontent.com/${REPO}/${BRANCH}/clap.py"
  log "Downloading clap.py from ${GITHUB_URL}"
  if command -v curl >/dev/null 2>&1; then
    curl -fsSL "$GITHUB_URL" -o "$SOURCE" || err "Failed to download clap.py"
  elif command -v wget >/dev/null 2>&1; then
    wget -q "$GITHUB_URL" -O "$SOURCE" || err "Failed to download clap.py"
  else
    err "Neither curl nor wget found. Install one of them."
  fi
  trap "rm -f '$SOURCE'" EXIT
fi

if [ ! -f "$SOURCE" ]; then
  err "clap.py not found at ${SOURCE}."
fi

cp "$SOURCE" "$TARGET"
chmod +x "$TARGET"
ok "Installed → ${TARGET}"

# ── Seed example presets ──────────────────────────────────────────────
"$PYTHON" "$TARGET" ls >/dev/null 2>&1 || true
log "Example presets seeded (if none existed)"

# ── Verify ────────────────────────────────────────────────────────────
if "$PYTHON" "$TARGET" ls >/dev/null 2>&1; then
  ok "clap is ready!"
  echo
  echo "  ${BOLD}Getting started:${NC}"
  echo "    clap                 open the TUI"
  echo "    clap ls              list presets"
  echo "    clap use <name>      switch profile"
  echo "    clap diff <name>     compare with current"
  echo "    clap restore <name>  rollback a backup"
  echo
else
  warn "Installed but a quick check failed — this may be fine."
  warn "Run 'clap ls' to verify manually."
fi
