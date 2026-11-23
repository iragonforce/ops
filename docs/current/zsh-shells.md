# Zsh shell configuration

## Authority

Repository: `iragonforce/ops`.

The installed configurations for `iragonforce` and `root` on
Nexus, Tensor and Qubit were imported into the repository on
2026-11-19.

The six configurations are authoritative source snapshots,
not evidence that an automated deployment has occurred.

## Source paths

| Host | User | Root |
| --- | --- | --- |
| nexus | `hosts/nexus/files/.zshrc` | `hosts/nexus/files/root/.zshrc` |
| tensor | `hosts/tensor/files/.zshrc` | `hosts/tensor/files/root/.zshrc` |
| qubit | `hosts/qubit/files/.zshrc` | `hosts/qubit/files/root/.zshrc` |

## Shared behavior

- Oh My Zsh with 13 built-in plugins.
- External autosuggestions, history-substring-search,
  syntax highlighting, you-should-use and zsh-z.
- The same Git-aware prompt layout and dirty indicator.
- Root username colour 167 and hostname colour 63.
- Independent history, with 100,000 entries.
- History autosuggestions ignore commands over 50 characters,
  using `ZSH_AUTOSUGGEST_HISTORY_IGNORE='?(#c51,)'`.
- Native Neovim, with `vim` and `vi` aliases.
- Atuin history integration and shared syntax colours.
- No automatic fastfetch.

The history suggestion limit does not limit
completion-generated suggestions.

## Host-specific behavior

- Qubit: Homebrew paths, macOS root home `/var/root`,
  and existing user tmux integration.
- Tensor: Hyprland startup, user tmux integration,
  root `capture` and `AUTO_CD`.
- Nexus: user SSH/tmux integration; root command timing,
  root-owned capture and Bitwarden helper.
- Root shells do not automatically attach to tmux.
- Root does not activate autoenv.
- Root history and authentication state remain independent.

Existing `.zprofile` and `.zshenv` files are not changed
by this task.

## Deployment and safety

Use `inventory/deployments.json` for source/target mappings.

The root targets are `/root/.zshrc` on Linux and
`/var/root/.zshrc` on Qubit. Require root ownership and
mode 0600 when installing. Git checkout permissions alone
do not enforce mode 0600.

All six configurations were imported from installed files.
Deployment records remain `deployed: false`, preserving
existing target files.

Before deployment, compare the source with the live target,
back up the target, run `zsh -n`, and verify interactive
startup. Preserve SSH access and maintain rollback access.

Do not commit root histories, Atuin databases, credentials,
Bitwarden runtime state, or local backup files.

Oh My Zsh and external plugin installations are separately
managed dependencies, not included in these six files.
