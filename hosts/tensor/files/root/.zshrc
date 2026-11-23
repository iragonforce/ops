# Tensor root — aligned with Qubit root and iragonforce.
# Root-owned plugins, separate history, no automatic tmux.

# Paths
path=(/usr/local/bin /usr/bin /bin /usr/local/sbin /usr/sbin /sbin $path)
typeset -U path

# Ghostty integration
if [[ -n "${GHOSTTY_RESOURCES_DIR:-}" &&
      -r "$GHOSTTY_RESOURCES_DIR/shell-integration/zsh/ghostty-integration" ]]; then
  source "$GHOSTTY_RESOURCES_DIR/shell-integration/zsh/ghostty-integration"
fi

# Oh My Zsh
export ZSH="$HOME/.oh-my-zsh"
export ZSH_CUSTOM="$ZSH/custom"
ZSH_THEME=""

# Preserve root's update policy
zstyle ':omz:update' mode disabled

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

# Root history
HISTFILE="$HOME/.zsh_history"
HISTSIZE=100000
SAVEHIST=100000

setopt append_history
setopt inc_append_history
setopt share_history
setopt hist_ignore_dups
setopt auto_cd

# Autosuggestions
if [[ -r "$ZSH_CUSTOM/plugins/zsh-autosuggestions/zsh-autosuggestions.zsh" ]]; then
  ZSH_AUTOSUGGEST_USE_ASYNC=true
  ZSH_AUTOSUGGEST_STRATEGY=(history completion)
  ZSH_AUTOSUGGEST_HIGHLIGHT_STYLE='fg=#808080'
  ZSH_AUTOSUGGEST_HISTORY_IGNORE='?(#c51,)'

  source "$ZSH_CUSTOM/plugins/zsh-autosuggestions/zsh-autosuggestions.zsh"

  bindkey '^[[C' autosuggest-accept
  bindkey '^F' autosuggest-accept
fi

# History substring search
if [[ -r "$ZSH_CUSTOM/plugins/zsh-history-substring-search/zsh-history-substring-search.zsh" ]]; then
  source "$ZSH_CUSTOM/plugins/zsh-history-substring-search/zsh-history-substring-search.zsh"

  bindkey '^[[A' history-substring-search-up
  bindkey '^[[B' history-substring-search-down
  bindkey -M vicmd 'k' history-substring-search-up
  bindkey -M vicmd 'j' history-substring-search-down
fi

# Shared external plugins
for plugin in you-should-use zsh-z; do
  file="$ZSH_CUSTOM/plugins/$plugin/$plugin.plugin.zsh"
  [[ -r "$file" ]] && source "$file"
done
unset plugin file

# autoenv intentionally disabled for root.

# Git-aware prompt
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

# Match Qubit root prompt exactly
PROMPT='%(?:%F{green}➜%f:%F{red}➜%f) %F{167}%n%f@%F{63}%m%f%F{red}$( __prompt_git_segment )%f %F{15}%~%f '

# Environment
export COLORTERM=truecolor
export LANG=C.UTF-8
export LC_ALL=C.UTF-8
unset NO_COLOR

# Native Neovim
export EDITOR="$(whence -p nvim 2>/dev/null)"
[[ -n "$EDITOR" ]] || export EDITOR=nvim
export VISUAL="$EDITOR"

alias vim='nvim'
alias vi='nvim'
alias py='python3'

if (( $+commands[watch] )); then
  alias watch='watch --color'
fi

# Preserve existing root capture integration
[[ -r /root/.config/zsh/capture.zsh ]] &&
  source /root/.config/zsh/capture.zsh

# Clipboard compatibility
if [[ -o interactive ]]; then
  _clipboard_key_noop() { return 0; }
  zle -N _clipboard_key_noop

  for keymap in emacs viins vicmd; do
    bindkey -M "$keymap" $'\e[25~' _clipboard_key_noop
    bindkey -M "$keymap" $'\e[26~' _clipboard_key_noop
    bindkey -M "$keymap" $'\e[1;2P' _clipboard_key_noop
    bindkey -M "$keymap" $'\e[1;2Q' _clipboard_key_noop
    bindkey -M "$keymap" $'\e[77101~' _clipboard_key_noop
  done
  unset keymap
fi

# Ghostty thin cursor inside tmux
if [[ -o interactive && -n "${TMUX:-}" ]]; then
  autoload -Uz add-zle-hook-widget
  _homelab_tmux_cursor_bar() { print -n -- $'\e[6 q'; }
  add-zle-hook-widget line-init _homelab_tmux_cursor_bar
fi

# Atuin — independent root history
if (( $+commands[atuin] )); then
  eval "$(atuin init zsh)"
fi

if [[ -o interactive ]] &&
   zle -l atuin-up-search >/dev/null 2>&1; then
  for keymap in emacs viins; do
    bindkey -M "$keymap" '^[[A' atuin-up-search
    bindkey -M "$keymap" '^[OA' atuin-up-search
  done
  unset keymap
fi

# Syntax highlighting — must be last
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
