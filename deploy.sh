#!/usr/bin/env bash
#
# deploy.sh — deploy this plugin into the local StreamController (Flatpak) install.
#
# Overlay-copies the plugin source into the StreamController plugins directory,
# keeping a timestamped backup so you can roll back. Optionally restarts the app
# (plugin code only loads at startup).
#
# Usage:
#   ./deploy.sh                 # back up + deploy (does NOT restart the app)
#   ./deploy.sh --restart       # back up + deploy + restart StreamController
#   ./deploy.sh --restart --yes # ...without the restart confirmation prompt
#   ./deploy.sh --clean         # mirror the source exactly (delete stray files,
#                               # except the store's VERSION file)
#   ./deploy.sh --rollback      # restore the most recent backup
#   ./deploy.sh --logs          # tail the StreamController log and exit
#   ./deploy.sh --help
#
# Env overrides:
#   PLUGIN_DIR=/custom/path ./deploy.sh
#   FLATPAK_APP=com.core447.StreamController ./deploy.sh

set -euo pipefail

# --- Configuration ----------------------------------------------------------
SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FLATPAK_APP="${FLATPAK_APP:-com.core447.StreamController}"
PLUGIN_DIR="${PLUGIN_DIR:-$HOME/.var/app/$FLATPAK_APP/data/plugins/HomeAssistantPlugin}"
LOG_FILE="$HOME/.var/app/$FLATPAK_APP/data/logs/logs.log"
# Backups live OUTSIDE plugins/ — StreamController tries to import every dir in
# plugins/ as a plugin, so a backup there would log import errors on each launch.
BACKUP_ROOT="${BACKUP_ROOT:-$HOME/.var/app/$FLATPAK_APP/data/plugin-backups}"

# Files/dirs that are dev-only and must never be deployed.
EXCLUDES=(--exclude='.git' --exclude='__pycache__' --exclude='*.pyc'
          --exclude='flake.nix' --exclude='flake.lock' --exclude='.direnv'
          --exclude='deploy.sh')

# --- Helpers ----------------------------------------------------------------
c_bold=$'\033[1m'; c_green=$'\033[32m'; c_yellow=$'\033[33m'; c_red=$'\033[31m'; c_reset=$'\033[0m'
info()  { printf '%s==>%s %s\n' "$c_green$c_bold" "$c_reset" "$*"; }
warn()  { printf '%s!! %s%s\n' "$c_yellow" "$*" "$c_reset"; }
die()   { printf '%sxx %s%s\n' "$c_red" "$*" "$c_reset" >&2; exit 1; }

usage() { awk 'NR==1{next} /^#/{sub(/^# ?/,""); print; next} {exit}' "${BASH_SOURCE[0]}"; exit 0; }

latest_backup() {
  # Most recent backup in BACKUP_ROOT, if any.
  ls -1dt "$BACKUP_ROOT"/HomeAssistantPlugin.bak-* 2>/dev/null | head -1 || true
}

restart_app() {
  command -v flatpak >/dev/null 2>&1 || die "flatpak not found; cannot restart $FLATPAK_APP."
  info "Stopping $FLATPAK_APP ..."
  flatpak kill "$FLATPAK_APP" 2>/dev/null || true
  sleep 1
  info "Launching $FLATPAK_APP ..."
  # Detach so this script can exit while the GUI keeps running.
  setsid flatpak run "$FLATPAK_APP" >/dev/null 2>&1 < /dev/null &
  disown 2>/dev/null || true
  info "Restarted. Give it a few seconds to load plugins."
}

# --- Argument parsing -------------------------------------------------------
DO_RESTART=0; ASSUME_YES=0; DO_CLEAN=0; DO_ROLLBACK=0; DO_LOGS=0
for arg in "$@"; do
  case "$arg" in
    --restart)  DO_RESTART=1 ;;
    --yes|-y)   ASSUME_YES=1 ;;
    --clean)    DO_CLEAN=1 ;;
    --rollback) DO_ROLLBACK=1 ;;
    --logs)     DO_LOGS=1 ;;
    --help|-h)  usage ;;
    *)          die "Unknown option: $arg (try --help)" ;;
  esac
done

# --- Modes that exit early --------------------------------------------------
if [[ "$DO_LOGS" == 1 ]]; then
  [[ -f "$LOG_FILE" ]] || die "Log file not found: $LOG_FILE"
  info "Tailing $LOG_FILE (Ctrl-C to stop)"
  exec tail -f "$LOG_FILE"
fi

if [[ "$DO_ROLLBACK" == 1 ]]; then
  backup="$(latest_backup)"
  [[ -n "$backup" ]] || die "No backup found matching ${PLUGIN_DIR}.bak-*"
  info "Rolling back to: $backup"
  rm -rf "$PLUGIN_DIR"
  mv "$backup" "$PLUGIN_DIR"
  info "Rollback complete."
  [[ "$DO_RESTART" == 1 ]] && restart_app
  exit 0
fi

# --- Pre-flight checks ------------------------------------------------------
[[ -f "$SOURCE_DIR/manifest.json" ]] || die "No manifest.json in $SOURCE_DIR — run from the plugin repo."
[[ -d "$HOME/.var/app/$FLATPAK_APP" ]] || die "StreamController Flatpak data dir not found for $FLATPAK_APP."
command -v rsync >/dev/null 2>&1 || die "rsync is required."

SRC_VERSION="$(grep -m1 '"version"' "$SOURCE_DIR/manifest.json" | sed -E 's/.*"version"[^"]*"([^"]+)".*/\1/')"
OLD_VERSION="$( [[ -f "$PLUGIN_DIR/manifest.json" ]] && grep -m1 '"version"' "$PLUGIN_DIR/manifest.json" | sed -E 's/.*"version"[^"]*"([^"]+)".*/\1/' || echo 'none')"

info "Source:  $SOURCE_DIR (v$SRC_VERSION)"
info "Target:  $PLUGIN_DIR (currently v$OLD_VERSION)"

# --- Backup -----------------------------------------------------------------
if [[ -d "$PLUGIN_DIR" ]]; then
  mkdir -p "$BACKUP_ROOT"
  BACKUP="$BACKUP_ROOT/HomeAssistantPlugin.bak-$(date +%Y%m%d-%H%M%S)"
  info "Backing up current install -> $BACKUP"
  cp -a "$PLUGIN_DIR" "$BACKUP"
else
  warn "No existing install at $PLUGIN_DIR — this is a fresh deploy."
  mkdir -p "$PLUGIN_DIR"
fi

# --- Deploy -----------------------------------------------------------------
RSYNC_ARGS=(-a "${EXCLUDES[@]}")
if [[ "$DO_CLEAN" == 1 ]]; then
  # Exact mirror, but never delete the store-generated VERSION file.
  RSYNC_ARGS+=(--delete --exclude='VERSION')
  info "Deploying (clean mirror) ..."
else
  info "Deploying (overlay) ..."
fi

rsync "${RSYNC_ARGS[@]}" "$SOURCE_DIR/" "$PLUGIN_DIR/"

NEW_VERSION="$(grep -m1 '"version"' "$PLUGIN_DIR/manifest.json" | sed -E 's/.*"version"[^"]*"([^"]+)".*/\1/')"
[[ "$NEW_VERSION" == "$SRC_VERSION" ]] \
  && info "Deployed v$NEW_VERSION ${c_green}OK${c_reset}" \
  || warn "Deployed manifest reports v$NEW_VERSION (expected v$SRC_VERSION)"

# --- Restart ----------------------------------------------------------------
if [[ "$DO_RESTART" == 1 ]]; then
  if [[ "$ASSUME_YES" != 1 ]]; then
    printf '%sRestart %s now? This will close the running app. [y/N] %s' "$c_yellow" "$FLATPAK_APP" "$c_reset"
    read -r reply
    [[ "$reply" =~ ^[Yy]$ ]] || { warn "Skipping restart. Restart manually to load the new code."; exit 0; }
  fi
  restart_app
else
  # --- To test it now -------------------------------------------------------
  printf '\n%s── To test it now ──%s\n' "$c_bold" "$c_reset"
  printf 'v%s is staged on disk%s. It only loads on restart:\n\n' \
    "$NEW_VERSION" "${BACKUP:+ (backup at $BACKUP)}"
  printf '    flatpak kill %s && flatpak run %s\n\n' "$FLATPAK_APP" "$FLATPAK_APP"
  printf 'Then exercise the change in StreamController. Roll back with:  %s --rollback\n' "$0"
  printf 'Or re-run with %s--restart%s to restart automatically.\n' "$c_bold" "$c_reset"
fi
