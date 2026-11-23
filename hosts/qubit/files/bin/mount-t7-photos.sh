#!/bin/zsh
# Mount the configured external T7 photo storage through its existing macOS integration. See mount-t7-photos.sh(1) for source and integration details.
if [ "${1-}" = '--help' ] && [ "$#" -eq 1 ]; then
  cat <<'OPS_USAGE_TEXT'
Mount the configured external T7 photo storage through its existing macOS integration.
Usage: mount-t7-photos.sh  [ARGUMENT ...]

Source: hosts/qubit/files/bin/mount-t7-photos.sh in ~/ops
See man mount-t7-photos.sh for the existing call sites and argument handling.
OPS_USAGE_TEXT
  exit 0
fi
set -u

T7_ROOT="/Volumes/t7"
IMAGE="$T7_ROOT/T7PhotosAPFS.sparsebundle"
APFS_VOL="/Volumes/T7PhotosAPFS"
LIBRARY="$APFS_VOL/Photos Library.photoslibrary"
LOG="$HOME/Library/Logs/mount-t7-photos.log"

log() {
  print -r -- "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >> "$LOG"
}

open_photos=0
if [[ "${1:-}" == "--open" ]]; then
  open_photos=1
fi

if [[ -d "$LIBRARY" ]]; then
  log "T7PhotosAPFS already mounted"
else
  if [[ ! -d "$IMAGE" ]]; then
    log "Sparsebundle not found at $IMAGE"
    exit 0
  fi

  log "Attaching $IMAGE"
  if ! /usr/bin/hdiutil attach "$IMAGE" -nobrowse >> "$LOG" 2>&1; then
    log "Attach failed"
    exit 1
  fi
fi

if [[ ! -d "$LIBRARY" ]]; then
  log "Library still missing after attach: $LIBRARY"
  exit 1
fi

log "Library ready: $LIBRARY"

if [[ "$open_photos" -eq 1 ]]; then
  log "Opening Photos library"
  /usr/bin/open -a Photos "$LIBRARY"
fi
