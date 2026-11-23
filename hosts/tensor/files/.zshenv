# Sourced for ALL zsh sessions (interactive, non-interactive, SSH)
export PATH="$HOME/.npm-global/bin:$HOME/.local/bin:$PATH"

# Make homelab launchers available in login, interactive and SSH command shells.
case ":$PATH:" in
  *":$HOME/.local/bin:"*) ;;
  *) export PATH="$HOME/.local/bin:$PATH" ;;
esac

# Tensor PATH normalization
typeset -U PATH path
if [[ "$OSTYPE" == linux* ]]; then
  path=("${(@)path:#/Users/iragonforce/.local/bin}")
else
  path=("${(@)path}")
fi
