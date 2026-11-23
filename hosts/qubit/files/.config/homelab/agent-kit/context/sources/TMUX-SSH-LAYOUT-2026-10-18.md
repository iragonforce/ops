# Tmux SSH and primary layout — 2026-10-18

User requested primary tmux sessions with windows 1 zsh, 2 nvim, 8 superfile and 9 btop on Qubit, Tensor and Nexus. Interactive SSH should detach the source client, attach the destination, and return to the source after `exit`.

## Changes

- Canonical `tmux-ensure-layout` now fills missing windows only, preserving existing windows and applications. Bootstrap and login call it. Auto-start selects Qubit `main`, Tensor `1`, Nexus `nexus` rather than the most recently active session. When a primary session has no client, login selects window 1 before attaching.
- Qubit `.zshrc` and Tensor `.zprofile` exit the SSH login shell after tmux detaches; Nexus already execs its tmux login helper. The helper's missing execute permission on Nexus was fixed in both the installed and kit copies.
- All three `.zshrc` files route interactive `exit` through `tmux-ssh-exit`, which detaches the most recently active client when it is SSH-backed. The existing source `tmux-ssh` runner then reattaches its original session. Local clients keep builtin `exit` behavior.
- Installed the two new helpers and updated bootstrap and auto-start helpers on all three hosts and their kit mirrors. No tmux server or current process was restarted.

## Checks and limits

- Syntax checks passed for changed Bash and zsh files. Nexus installed login helper is executable. SSH logins with `TERM=dumb` now select `xterm-256color` on Qubit and Tensor before tmux starts.
- Primary window inventories after filling gaps: Qubit `main` has 1 zsh, 2 nvim, 8 superfile, 9 btop; Tensor `1` has these plus existing 3 hermes; Nexus `nexus` has these plus existing 3, 4 and 6. The nested Bash shell previously occupying Nexus window 1 was preserved at window 10; a new zsh window occupies 1. Other sessions were preserved.
- Controlled interactive terminal connections attached to all three primary sessions. `exit` detached each remote client and closed its SSH connection without removing window 1. A full Qubit → Tensor → Qubit cycle returned to the original Qubit tmux session after `exit` on Tensor. This does not establish Ghostty key behavior on the physical desktop.
- Tensor's old window 1 zsh predated the new exit function; the first controlled `exit` closed that window. It was recreated with the new startup and the subsequent exit cycle passed. Nexus's preserved Bash window 10 does not load the zsh exit function.
- Tensor's `qubit` alias still targets Qubit's currently unreachable wired address `192.168.1.4`. The existing `qubit-ts` Tailscale route succeeded and was used for Qubit checks. No SSH aliases or routing were changed.

## Rollback

- Qubit original `.zshrc` and `.zprofile` plus prior installed bootstrap and auto-start are in this task's `work/tmux-backup`. The prior canonical bootstrap and auto-start equal those installed copies.
- Tensor originals are in `/home/iragonforce/.local/state/tmux-fix-20261018/`; Nexus originals are in the matching path on Nexus. Restore those host-specific files, then remove `tmux-ensure-layout` and `tmux-ssh-exit` from the kit and `~/.local/bin` on all three hosts. Restore the previous README, AGENTS and context text from this change record if reversing the policy. Existing windows can be left alone.
- If restoring Nexus's former numbering, first move the new zsh window 1 to a free index or close it only after confirming it has no work, then move preserved window 10 back to 1. The old Bash process remains in window 10 until explicitly changed.
