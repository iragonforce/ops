# NEXUS — single SSH tmux session must bootstrap before the main shell.
export PATH="$HOME/.local/bin:$PATH"
if [[ -o interactive && -n "${SSH_TTY:-}" && -z "${TMUX:-}" && -t 0 && -t 1 ]]; then
  if [[ ${TERM:-dumb} == dumb ]] || ! infocmp "${TERM:-dumb}" >/dev/null 2>&1; then
    export TERM=xterm-256color
  fi
  exec "$HOME/.config/tmux/session" start
fi

# =============================================================================
# Shared Zsh configuration — Qubit reference, adapted by host
# =============================================================================

# Local executables need to be available before plugins and helper scripts.
export PATH="$HOME/.local/bin:$HOME/bin:$PATH"

if [[ -n "${GHOSTTY_RESOURCES_DIR:-}" && -r "${GHOSTTY_RESOURCES_DIR}/shell-integration/zsh/ghostty-integration" ]]; then
  source "${GHOSTTY_RESOURCES_DIR}/shell-integration/zsh/ghostty-integration"
fi

export ZSH="$HOME/.oh-my-zsh"
ZSH_THEME=""
plugins=(
  git
  colored-man-pages
  command-not-found
  extract
  safe-paste
  web-search
  npm
  yarn
  kubectl
  docker
  pipenv
  pip
  python
)

source "$ZSH/oh-my-zsh.sh"

# Qubit's history policy.
HISTFILE="$HOME/.zsh_history"
HISTSIZE=100000
SAVEHIST=100000
setopt append_history
setopt inc_append_history
setopt share_history
setopt hist_ignore_dups

# External plugins: source after Oh My Zsh. Syntax highlighting is added last.
if [[ -f "$ZSH_CUSTOM/plugins/zsh-autosuggestions/zsh-autosuggestions.zsh" ]]; then
  ZSH_AUTOSUGGEST_USE_ASYNC=true
  ZSH_AUTOSUGGEST_STRATEGY=(history completion)
  ZSH_AUTOSUGGEST_HIGHLIGHT_STYLE='fg=#808080'
  ZSH_AUTOSUGGEST_HISTORY_IGNORE='?(#c51,)'
  source "$ZSH_CUSTOM/plugins/zsh-autosuggestions/zsh-autosuggestions.zsh"
  bindkey '^[[C' autosuggest-accept
  bindkey '^F' autosuggest-accept
fi

if [[ -f "$ZSH_CUSTOM/plugins/zsh-history-substring-search/zsh-history-substring-search.zsh" ]]; then
  source "$ZSH_CUSTOM/plugins/zsh-history-substring-search/zsh-history-substring-search.zsh"
  bindkey '^[[A' history-substring-search-up
  bindkey '^[[B' history-substring-search-down
  bindkey -M vicmd 'k' history-substring-search-up
  bindkey -M vicmd 'j' history-substring-search-down
fi

if [[ -f "$ZSH_CUSTOM/plugins/you-should-use/you-should-use.plugin.zsh" ]]; then
  source "$ZSH_CUSTOM/plugins/you-should-use/you-should-use.plugin.zsh"
fi
if [[ -f "$ZSH_CUSTOM/plugins/zsh-z/zsh-z.plugin.zsh" ]]; then
  source "$ZSH_CUSTOM/plugins/zsh-z/zsh-z.plugin.zsh"
fi
if [[ -f "$ZSH_CUSTOM/plugins/autoenv/autoenv.plugin.zsh" ]]; then
  source "$ZSH_CUSTOM/plugins/autoenv/autoenv.plugin.zsh"
fi

# Identical prompt on all hosts: status, user@host, Git branch (+dirty *), CWD.
setopt PROMPT_SUBST
__prompt_git_segment() {
  local branch dirty
  branch=$(command git symbolic-ref --short HEAD 2>/dev/null \
    || command git describe --tags --exact-match HEAD 2>/dev/null \
    || command git rev-parse --short HEAD 2>/dev/null) || return 0
  dirty=''
  [[ -n "$(command git status --porcelain 2>/dev/null)" ]] && dirty='*'
  print -r -- " git:(${branch}${dirty})"
}

if (( EUID == 0 )); then
  PROMPT='%(?:%F{green}➜%f:%F{red}➜%f) %F{red}%n%f@%F{yellow}%m%f%F{red}$( __prompt_git_segment )%f %F{15}%~%f '
else
  PROMPT='%(?:%F{yellow}➜%f:%F{red}➜%f) %F{yellow}%n%f@%F{63}%m%f%F{red}$( __prompt_git_segment )%f %F{15}%~%f '
fi

export COLORTERM=truecolor
export LANG=C.UTF-8
export LC_ALL=C.UTF-8
unset NO_COLOR

# Preserve Nexus/Tensor's command execution time display and tmux metric.
zmodload zsh/datetime
autoload -Uz add-zsh-hook
typeset -g __codex_cmd_start=0
typeset -g __codex_cmd_name=''

__codex_excluded_commands=(vim nvim vi ssh ping)

__codex_extract_command_name() {
  local cmd="${1#"${1%%[![:space:]]*}"}"
  local -a words
  words=(${(z)cmd})
  local word
  for word in "${words[@]}"; do
    case "$word" in
      sudo|command|builtin|noglob|nocorrect|env|time) continue ;;
      *=*) continue ;;
      *) print -r -- "$word"; return 0 ;;
    esac
  done
  return 1
}

__codex_preexec() {
  __codex_cmd_start=$EPOCHREALTIME
  __codex_cmd_name="$(__codex_extract_command_name "$1")"
}

__codex_precmd() {
  local exit_code=$?
  [[ $__codex_cmd_start == 0 ]] && return
  local start_time=$__codex_cmd_start
  local cmd_name="$__codex_cmd_name"
  __codex_cmd_start=0
  __codex_cmd_name=''
  local elapsed_ms=$(( (EPOCHREALTIME - start_time) * 1000.0 ))
  local elapsed_ms_fmt
  printf -v elapsed_ms_fmt '%.2f ms' "$elapsed_ms"
  if [[ -n "${TMUX:-}" ]] && (( $+commands[tmux] )); then
    tmux set-option -gq @last_cmd_ms "${elapsed_ms_fmt}" 2>/dev/null || true
  fi
  (( ${#__codex_excluded_commands[(I)$cmd_name]} )) && return
  local symbol color
  if (( exit_code == 0 )); then
    symbol='✓'; color=green
  else
    symbol='✗'; color=red
  fi
  print -P "%F{$color}${symbol}%f %F{242}• ${elapsed_ms_fmt}%f"
}

add-zsh-hook preexec __codex_preexec
add-zsh-hook precmd __codex_precmd

# NEXUS — native Neovim and existing SSH integration.
unalias dtop 2>/dev/null || true
unalias gc 2>/dev/null || true
export EDITOR="$(whence -p nvim 2>/dev/null)"
[[ -n "$EDITOR" ]] || export EDITOR=nvim
export VISUAL="$EDITOR"



# Keep the short editor commands, but do not wrap the actual nvim binary.
alias vim='nvim'
alias vi='nvim'

# User shell integrations.
[[ -r "$HOME/.config/shell/capture.sh" ]] && source "$HOME/.config/shell/capture.sh"
[[ -r "$HOME/.config/bws/helpers.zsh" ]] && source "$HOME/.config/bws/helpers.zsh"

if (( $+commands[watch] )); then
  alias watch='watch --color'
fi

# Atuin takes precedence for Up Arrow in emacs/viins, matching Qubit.
if (( $+commands[atuin] )); then
  eval "$(atuin init zsh)"
fi
if [[ -o interactive ]] && zle -l atuin-up-search >/dev/null 2>&1; then
  for _atuin_keymap in emacs viins; do
    bindkey -M "$_atuin_keymap" '^[[A' atuin-up-search
    bindkey -M "$_atuin_keymap" '^[OA' atuin-up-search
  done
  unset _atuin_keymap
fi

# Preserve tmux/Ghostty clipboard key compatibility.
if [[ -o interactive ]]; then
  _clipboard_key_noop() { return 0; }
  zle -N _clipboard_key_noop
  for _clipboard_keymap in emacs viins vicmd; do
    bindkey -M "$_clipboard_keymap" $'\e[25~' _clipboard_key_noop
    bindkey -M "$_clipboard_keymap" $'\e[26~' _clipboard_key_noop
    bindkey -M "$_clipboard_keymap" $'\e[1;2P' _clipboard_key_noop
    bindkey -M "$_clipboard_keymap" $'\e[1;2Q' _clipboard_key_noop
    bindkey -M "$_clipboard_keymap" $'\e[77101~' _clipboard_key_noop
  done
  unset _clipboard_keymap
fi

if [[ -o interactive && -n "${TMUX:-}" ]]; then
  autoload -Uz add-zle-hook-widget
  _homelab_tmux_cursor_bar() { print -n -- $'\e[6 q'; }
  add-zle-hook-widget line-init _homelab_tmux_cursor_bar
fi

# Final plugin: must load after other widgets, aliases and functions.
if [[ -r "$ZSH_CUSTOM/plugins/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh" ]]; then
  source "$ZSH_CUSTOM/plugins/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh"
  ZSH_HIGHLIGHT_STYLES[command]='fg=#00ff00,bold'
  ZSH_HIGHLIGHT_STYLES[builtin]='fg=#00ff00,bold'
  ZSH_HIGHLIGHT_STYLES[function]='fg=#00ff00,bold'
  ZSH_HIGHLIGHT_STYLES[alias]='fg=#00ff00,bold'
  ZSH_HIGHLIGHT_STYLES[unknown-token]='fg=#ff0000,bold'
  ZSH_HIGHLIGHT_STYLES[path]='fg=#ffffff'
  ZSH_HIGHLIGHT_STYLES[single-quoted-argument]='fg=#ffff00'
  ZSH_HIGHLIGHT_STYLES[double-quoted-argument]='fg=#ffff00'
fi

# Attach to the managed session from an interactive local terminal.
if [[ -o interactive && -z ${TMUX:-} && -t 0 && -t 1 && ${TERM:-} != dumb ]]; then
  "$HOME/.config/tmux/session" start
  if [[ -n ${TMUX_AUTO_EXIT_ON_DETACH:-} ]]; then
    builtin exit
  fi
fi

# Bare tmux attaches; subcommands use the native executable.
tmux() {
  if (( $# == 0 )); then
    if [[ -n ${TMUX:-} ]]; then
      command tmux display-message 'Already inside tmux: #{session_name}'
    else
      "$HOME/.config/tmux/session" start
    fi
  else
    command tmux "$@"
  fi
}
typeset -U path
path=(/usr/local/sbin /usr/sbin /sbin $path)
