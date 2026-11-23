# Tensor tmux login and Cmd+C — 2026-10-17

## Before

- `ssh tensor` printed an `IndexError` from `~/.local/bin/tmux-ensure-layout` at `old[3]`. Tensor tmux 3.8 had sessions `1` and `main`, each with one window. User40 was bound in both copy-mode tables, but a failed login could leave the user outside tmux, where CSI 77101~ appeared as `7101~`.
- Tensor's installed layout helper had newer logic that preserved occupied windows, unlike the stale canonical kit helper. Its `run(...).strip()` removed empty trailing tab fields from the window inventory.
- Tensor's Python copy helper discovered the graphical Wayland environment and used `wl-copy` even for an SSH-attached macOS terminal.

## Changes

- Updated canonical `tmux/helpers/tmux-ensure-layout` with Tensor's preserve-running-windows logic. Captured tmux output now strips only newline endings, and the inventory pads missing optional fields before accessing layout role. Installed the helper in Tensor's `~/.local/bin` and kit mirror.
- Updated canonical `tmux/helpers/tmux-copy` so Linux tmux copies use `tmux load-buffer -w` and OSC 52 for the attached terminal. macOS retains its existing `pbcopy` and readback path; paste logic is unchanged. Installed the helper in Tensor's local bin and kit mirror.
- Ran the repaired layout helper on current Tensor session `1`. It kept its original window 1 pane and added expected windows 2, 3, 8 and 9. No session or application was killed. Tensor's tmux server was not restarted. No tmux config or key file was changed.

## Checks and limits

- A second layout-helper invocation exited 0 with no traceback. Tensor session `1` has windows 1 zsh, 2 nvim, 3 Hermes, 8 Superfile, 9 btop; `main` remains one zsh window.
- An interactive SSH login using a controlled terminal attached to session `1` with terminal type `xterm-ghostty`, and the captured output had no traceback.
- A temporary SSH tmux client received CSI 77101~ in copy mode. The key exited copy mode and displayed `Copy sent: 17 characters, 1 lines`; the terminal stream contained an OSC 52 write. The temporary session was removed.
- The controlled pseudo-terminal captured OSC 52 instead of forwarding it to macOS Ghostty. Physical drag/Cmd+C clipboard acceptance from the user's normal terminal remains pending. Clipboard text was not printed or saved. No formal tests were added or run.

## Rollback

Tensor backup directory: `/home/iragonforce/.local/state/tensor-tmux-copy-20261017-144046`. Restore `tmux-ensure-layout.before` to `~/.local/bin/tmux-ensure-layout`, `tmux-copy.before` to `~/.local/bin/tmux-copy`, `kit-tmux-ensure-layout.before` to `~/.config/homelab/agent-kit/tmux/helpers/tmux-ensure-layout`, and `kit-tmux-copy.before` to `~/.config/homelab/agent-kit/tmux/helpers/tmux-copy`; preserve executable modes. The `tmux-copy.before` file was copied from Tensor's unchanged kit mirror after the installed helper was replaced and matched the Qubit old-helper backup by SHA-256.

Qubit canonical backups: `/Users/iragonforce/.local/state/tensor-tmux-copy-20261017-144046/qubit-kit-tmux-ensure-layout.before` and `qubit-kit-tmux-copy.before`. Restore them to matching kit helper paths. Existing tmux sessions do not require a restart for either rollback. The newly added Tensor windows can be left in place; remove them only after confirming they contain no unsaved work.
