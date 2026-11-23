#!/bin/zsh
# Reconcile the existing macOS Dock, Homebrew and iCloud integration. See dock-brew-icloud-sync.sh(1) for source and integration details.
if [ "${1-}" = '--help' ] && [ "$#" -eq 1 ]; then
  cat <<'OPS_USAGE_TEXT'
Reconcile the existing macOS Dock, Homebrew and iCloud integration.
Usage: dock-brew-icloud-sync.sh  [ARGUMENT ...]

Source: hosts/qubit/files/.local/bin/dock-brew-icloud-sync.sh in ~/ops
See man dock-brew-icloud-sync.sh for the existing call sites and argument handling.
OPS_USAGE_TEXT
  exit 0
fi
set -euo pipefail

LOG_DIR="$HOME/.local/state"
LOG_FILE="$LOG_DIR/dock-brew-icloud-sync.log"
STATE_FILE="$LOG_DIR/dock-brew-icloud-sync.state"
LOCK_DIR="$LOG_DIR/dock-brew-icloud-sync.lock"
ICLOUD_MARKER_DIR="$HOME/Library/Mobile Documents/com~apple~CloudDocs/.sync-markers"
ICLOUD_MARKER_FILE="$ICLOUD_MARKER_DIR/dock-trigger-sync.txt"

mkdir -p "$LOG_DIR" "$ICLOUD_MARKER_DIR"

log() {
  printf '%s %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*" >> "$LOG_FILE"
}

notify() {
  local title="$1"
  local body="$2"
  osascript -e "display notification \"$body\" with title \"$title\"" >/dev/null 2>&1 || true
}

# single-run lock
if ! mkdir "$LOCK_DIR" 2>/dev/null; then
  exit 0
fi
cleanup_lock() {
  rmdir "$LOCK_DIR" 2>/dev/null || true
}
trap cleanup_lock EXIT

# Detect any attached Thunderbolt device (dock or peripheral)
if ioreg -p IOService -r -n AppleThunderboltPort -l 2>/dev/null | grep -q 'PortMicroFirmwareVersion'; then
  current_state="connected"
else
  current_state="disconnected"
fi

previous_state="unknown"
if [[ -f "$STATE_FILE" ]]; then
  previous_state="$(<"$STATE_FILE")"
fi

printf '%s\n' "$current_state" > "$STATE_FILE"

if [[ "$previous_state" == "connected" || "$current_state" != "connected" ]]; then
  exit 0
fi

log "Dock/Thunderbolt connection detected. Running Homebrew maintenance."
notify "Dock Automation" "Homebrew update started"

# Ensure Homebrew is in PATH for launchd
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"

brew_failed=0

if command -v brew >/dev/null 2>&1; then
  brew update >> "$LOG_FILE" 2>&1 || { log "brew update failed"; brew_failed=1; }
  brew upgrade >> "$LOG_FILE" 2>&1 || { log "brew upgrade failed"; brew_failed=1; }
  brew cleanup >> "$LOG_FILE" 2>&1 || { log "brew cleanup failed"; brew_failed=1; }
else
  log "brew not found in PATH"
  brew_failed=1
fi

# Force/nudge iCloud sync by mutating a file in iCloud Drive.
printf '%s\n' "Dock trigger sync at $(date '+%Y-%m-%d %H:%M:%S')" > "$ICLOUD_MARKER_FILE" || log "iCloud marker write failed"

# Optional extra nudge: notify CloudDocs daemon.
killall -HUP bird >/dev/null 2>&1 || true

log "Dock-trigger routine finished."
if [[ "$brew_failed" -eq 0 ]]; then
  notify "Dock Automation" "Homebrew update finished successfully"
else
  notify "Dock Automation" "Homebrew update finished with errors (see log)"
fi
