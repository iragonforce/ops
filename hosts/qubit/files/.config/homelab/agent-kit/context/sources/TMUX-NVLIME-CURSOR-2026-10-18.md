# Tmux boot, Tensor NVlime and prompt cursor, 2026-10-18

## Changes

- The kit installer copied `tmux-ensure-layout` and then deleted it as a supposedly legacy helper. Removed that deletion. Restored the maintained executable on Qubit, Tensor and Nexus. Tensor's post-reboot primary session `1` was absent; created it with windows 1 zsh, 2 nvim, 8 superfile and 9 btop. Existing Tensor session `0` and its running panes were preserved.
- Tensor had SBCL and the NVlime plugin, but no Quicklisp installation. Downloaded the official Quicklisp bootstrap, matched its published SHA-256, and installed it in `~/quicklisp`. Loaded NVlime's Lisp dependencies through Quicklisp. Tensor Neovim now gives NVlime's SBCL server the Quicklisp setup path without modifying ordinary SBCL startup, and starts one server when the first Lisp buffer opens. Its connection check now treats both Lua nil and `vim.NIL` as disconnected.
- Applied the NVlime server builder to Tensor's existing Neovim process and started its SBCL server there. The live editor reported one server and an active connection.
- Qubit, Tensor and Nexus Zsh prompt configuration now emits a steady thin bar cursor when a Zsh line editor starts inside tmux. It uses Zsh's hook helper so other line-init hooks are retained. Qubit and Tensor Ghostty configs also set the default cursor shape to `bar`, so a tmux cursor reset returns to a bar instead of a block; Neovim can still set its mode-specific shape. Already running shells need `source ~/.zshrc` or a new shell for the Zsh hook.

## Operational checks and limits

- The restored helper is executable on all three hosts. Tensor `1` has the expected four windows. Tensor-to-Qubit SSH saw the restored Qubit helper.
- Tensor's Quicklisp/NVlime Lisp loader completed and the existing Neovim server reported `servers=1 connected=1` after live startup. A headless Neovim attempt could not open NVlime's UI because the plugin requires an attached UI; this did not indicate a live editor failure.
- The changed Neovim Lua and all three Zsh files passed syntax checks. Ghostty configs validated on Qubit and Tensor, and effective configs report `cursor-style = bar`. Tensor's two running Ghostty processes reloaded and survived; Qubit had no running Ghostty process to reload. Cursor appearance still needs visual confirmation.

## Rollback

- Qubit prechange installer, Zsh and both Ghostty configs: task `work/reboot-fix-backup/` under `/Users/iragonforce/Documents/Codex/2026-10-18/can-you-fix-tmux-x20/`.
- Tensor prechange Neovim init, Zsh and Ghostty config: `~/.local/state/clipboard-20261018/nvim-init.before-nvlime-fix`, `zshrc.before-cursor-fix` and `ghostty.before-cursor-fix`. Quicklisp and the installation logs are under `~/quicklisp` and `~/.local/state/nvlime-20261018`; remove Quicklisp only after ending dependent SBCL sessions. The original Tensor `0` tmux session remains untouched.
- Nexus prechange Zsh config: `~/.local/state/clipboard-20261018/zshrc.before-cursor-fix`. Restore a backed-up file while preserving later edits. The maintained `tmux-ensure-layout` should remain installed unless the corresponding bootstrap and auto-start calls are also removed.
