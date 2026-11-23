# Qubit Ghostty Cmd+V over SSH — 2026-10-17

## Change

User reported Cmd+V printing `7102~` on Tensor and Nexus over SSH. Qubit Ghostty mapped `super+v` to CSI 77102~. Nexus did not bind User41, and Tensor's User41 helper could only read Tensor's clipboard, not Qubit's Mac clipboard through SSH. OSC 52 supports the copy direction, not remote clipboard readback.

Changed `super+v` to Ghostty's `paste_from_clipboard` in both Qubit config locations: active macOS `~/Library/Application Support/com.mitchellh.ghostty/config` and `~/.config/ghostty/config`. `super+c` continues to send CSI 77101~ for tmux copying; Ctrl+C remains normal. Ctrl+Shift+V remains native paste. Sent the running Ghostty application its default Cmd+Shift+, reload shortcut; no terminal or tmux session was restarted.

## Checks and limit

`ghostty +validate-config` exited 0. `ghostty +show-config --changes-only` read back `super+v=paste_from_clipboard` and `super+c=csi:77101~` from the effective macOS config. The actual macOS-to-SSH paste needs a physical Cmd+V check in the user's existing terminal; no clipboard data was read, printed or stored during this change.

## Rollback

Backups are in `/Users/iragonforce/.local/state/ghostty-cmd-v-20261017/`: `mac-app-config.before` and `config.before`. Restore each file to its corresponding path above and trigger Ghostty Reload Config (Cmd+Shift+,). Restoring the old mapping will restore CSI 77102~ behavior.
