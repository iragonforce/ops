# Nexus tmux Cmd+C and outbound SSH — 2026-10-17

## Before

- Nexus tmux 3.5a had one active `nexus` session with windows 1, 2, 3, 4, 5, 8 and 9. The required applications remained running. Mouse was off, set-clipboard was on, and User40 was absent.
- `~/.tmux.conf` linked to the Nexus agent-kit mirror. Nexus `~/.local/bin/tmux-copy` handled local clipboard tools or a basic tmux buffer; it did not show counts.
- Nexus already had separate `qubit_ed25519` and `tensor_ed25519` identities. Both public keys were present in the corresponding hosts' authorized keys. Nexus could reach Tensor, but `qubit` resolved to Qubit's unreachable Wi-Fi address.

## Changes

- Canonical kit `tmux/tmux.conf` now loads `tmux/nexus-clipboard.conf` on Nexus and retains the existing `tmux/clipboard.conf` path on other hosts. The overlay was installed on Nexus and sourced live. It maps CSI 77101~ to User40 and binds that key in both copy-mode tables, enables tmux mouse selection and the terminal clipboard feature, and shows a 2-second count message.
- Installed the existing canonical Python `tmux-copy` helper on Nexus. In Nexus's headless environment it uses `tmux load-buffer -w` for OSC 52 and records a transient character/line count. Clipboard text is never logged.
- Changed Nexus SSH `qubit` / `qubit.homelab.lan` HostName to wired `192.168.1.4`. Its HostKeyAlias, strict checking, dedicated identity and known-host file remain the same. Tensor SSH config was unchanged. No keys or authorized-key entries were modified.

## Checks and limits

- Nexus and Qubit tmux configs sourced successfully without server restart. Nexus still had the same seven windows. User40 binding, mouse=on, set-clipboard=on and the attached client's clipboard feature read back.
- Nexus's existing known-host records matched Qubit's and Tensor's ED25519 host keys during strict SSH negotiation. Both accepted their existing dedicated Nexus public keys; `ssh qubit hostname` and `ssh tensor hostname` returned the expected host names.
- A synthetic Nexus helper copy returned `Copy sent: 12 characters, 1 lines`; Qubit's clipboard count was 12 characters/one line. The synthetic copy replaced Qubit's clipboard; its contents were neither printed nor saved.
- An isolated pseudo-terminal probe did not forward input reliably; it is not evidence for a real Ghostty Cmd+C press. Physical drag/Cmd+C acceptance remains pending. No formal tests were added or run.

## Rollback

Nexus backup directory: `/home/iragonforce/.local/state/nexus-tmux-ssh-20261017-143411`. Restore `tmux.conf.before` to `~/.config/homelab/agent-kit/tmux/tmux.conf`, `tmux-copy.before` to `~/.local/bin/tmux-copy` and `ssh-config.before` to `~/.ssh/config`, preserving their original modes. Remove only `~/.config/homelab/agent-kit/tmux/nexus-clipboard.conf`, then run `tmux source-file ~/.tmux.conf`. Existing tmux sessions stay running.

Qubit canonical backup: `/Users/iragonforce/.local/state/nexus-tmux-ssh-20261017-143411/qubit-kit-tmux.conf.before`. Restore it to the kit's `tmux/tmux.conf`, remove the kit's `tmux/nexus-clipboard.conf`, then source Qubit's `~/.tmux.conf`. No authorized-key or known-host rollback is needed.
