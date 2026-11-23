#!/bin/zsh
# Start a login Zsh with the existing Ghostty debug environment. See ghostty-debug-shell.sh(1) for source and integration details.
if [ "${1-}" = '--help' ] && [ "$#" -eq 1 ]; then
  cat <<'OPS_USAGE_TEXT'
Start a login Zsh with the existing Ghostty debug environment.
Usage: ghostty-debug-shell.sh 

Source: hosts/qubit/files/.local/bin/ghostty-debug-shell.sh in ~/ops
See man ghostty-debug-shell.sh for the existing call sites and argument handling.
OPS_USAGE_TEXT
  exit 0
fi
LOG="$HOME/ghostty-shell-trace.txt"
{
  echo "=== GHOSTTY SHELL TRACE ==="
  date
  echo "SHELL=$SHELL"
  echo "0=$0"
  echo "FLAGS=$-"
  echo "TERM=$TERM"
  echo "TERM_PROGRAM=${TERM_PROGRAM-}"
  echo "GHOSTTY_RESOURCES_DIR=${GHOSTTY_RESOURCES_DIR-}"
  echo "GHOSTTY_BIN_DIR=${GHOSTTY_BIN_DIR-}"
  echo "PATH=$PATH"
  echo
  echo "=== ZSH STARTUP FILES ==="
  for f in ~/.zshenv ~/.zprofile ~/.zshrc ~/.zlogin /etc/zshenv /etc/zprofile /etc/zshrc /etc/zlogin; do
    [[ -e "$f" ]] && echo "--- $f" && ls -ld "$f"
  done
  echo
  echo "=== FASTFETCH / PROMPT STATE ==="
  command -v fastfetch || true
  typeset -p FASTFETCH_RUN 2>/dev/null || true
  setopt | grep -i prompt || true
  print -r -- "PROMPT=$PROMPT"
  whence -v git_prompt_info || true
  echo
  echo "=== ENV FILTER ==="
  env | egrep '^(TERM|TERM_PROGRAM|COLORTERM|PATH|ZDOTDIR|ZSH|GHOSTTY_|XDG_CONFIG_HOME|HOME)=' | sort
  echo
  echo "=== END TRACE ==="
} > "$LOG" 2>&1
exec /bin/zsh --login
