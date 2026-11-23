# Hosts and execution boundaries

2026-10-16: New Hermes CLI launches on Qubit, Tensor and Nexus use the shared `qubit` profile. The original `tensor` and `nexus` profile histories stay intact and are accessible with explicit `hermes -p <profile>`. Existing live sessions are not restarted. This is a shared identity/session store, not a copy of machine-local project files; Nexus Docker remains the execution host. Qubit is reachable from Nexus's Hermes container via nested SSH through Tensor on Qubit's Tailscale address, not directly from the container at this check. Rollback and dated checks: kit CHANGELOG.md entry on shared Hermes identity.

| Host | Role / OS | LAN | Tailscale |
|---|---|---|---|
| Nexus | NAS, Docker, KVM; Debian 13 | 192.168.1.2 | 100.96.255.81 |
| Tensor | Desktop; Arch, Hyprland, RTX 5070 + AMD iGPU | 192.168.1.3 | 100.114.178.50 |
| Qubit | Control Mac; macOS | Ethernet 192.168.1.4; Wi-Fi 192.168.1.102 | 100.103.67.56 |
| UDR7 | UniFi gateway/router | 192.168.1.1 | Use existing authenticated management path |
| Bell | Upstream ISP gateway; Wi-Fi off | 192.168.100.1 | Not a tailnet host |

Nexus and Tensor local names: `nexus.homelab.lan`, `tensor.homelab.lan`. Qubit Wi-Fi: `qubit.homelab.lan`; wired: `qubit-wired.homelab.lan`.

Tailnet suffix: `tail4e4f0f.ts.net`. Phone `signal` was reported at `100.109.161.19`; verify its current identity before changing access rules.

Human SSH aliases `nexus`, `tensor`, `qubit` exist on the control machines. Existing key trust is retained. A changed host key must be verified through a trusted path before updating known_hosts.

On 2026-10-14 Tensor's Tailscale SSH interception was disabled (`tailscale set --ssh=false`). OpenSSH now handles connections over both LAN and Tailscale using existing keys. Qubit's `ssh tensor`, direct LAN SSH and Tailscale SSH with the trusted host-key alias all worked after that change. This was not a key rotation.

## Hermes on Nexus — live checked 2026-10-14

- Running healthy: `nousresearch/hermes-agent:v0.21.6`, pinned digest in the live inventory and original Checkmk/Hermes source note.
- Host command `/usr/local/bin/hermes` executes the container CLI. It defaults to `/opt/data/workspace` inside the container.
- Host `hermes-login` prompts for ChatGPT OAuth or an OpenAI API key. It uses the existing private auth helper and restarts the Hermes container after successful login.
- Persistent Hermes home: host `/srv/containers/data/hermes/data` → container `/opt/data`.
- This pack: host `/srv/containers/data/hermes/data/workspace/homelab-context` → container `/opt/data/workspace/homelab-context`.
- Existing `/opt/data/workspace/AGENTS.md`, global `/opt/data/SOUL.md`, provider settings, credentials, session history and memories are preserved.
- Container `/mnt/fast` maps the host's active `/srv/containers/data`, not the original host `/mnt/fast` pool root.
- Container `/mnt/bulk` is read-only except the existing writable `/mnt/bulk/data` submount. `/openclaw` is a read-only legacy reference.
- The host Docker socket is already mounted. `docker exec` through the host wrapper runs as container root. This does not make arbitrary host `/etc` paths available as container `/etc`.

No provider login, model inference or external message was performed during preparation of this pack. The installed CLI was checked for the commands documented in `README.md`.

## Nexus terminal selection — 2026-10-14 follow-up

At the user's request, tmux mouse capture is now off in its persistent config and running server. Neovim's init sets `vim.opt.mouse = ""`. This allows ordinary terminal drag selection and the local terminal Copy shortcut. Preserve that choice; do not silently restore mouse capture. Configuration backups are under `/home/iragonforce/.local/state/terminal-selection/20261014-210228/`. No editor was running when the setting changed.

## 2026-10-15 — Tensor TMU SSH access

Copied Qubit's existing private TMU key from `~/.ssh/trial` to Tensor `~/.ssh/id_tmu` and its public companion, with mode 0600. Added Tensor `~/.ssh/config.d/tmu.conf`: `tmu` / `moon.cs.torontomu.ca`, user `sulanov`, that identity only, strict host checking against `~/.ssh/known_hosts_tmu` populated from Qubit's existing trust. Verified a noninteractive `ssh tmu` login as `sulanov`; remote hostname reported `thebe`. No pending work. Rollback: remove only these four newly created Tensor files; existing SSH configuration and Qubit key are unchanged. No backups created.

## 2026-10-15 — Nexus Neovim and Hermes repairs

Observed Neovim dashboard paste E21 in tmux and Telescope startup failure because Debian Neovim 0.10.4 was older than the installed plugin requirement. Installed official Neovim v0.12.6 under `/opt/neovim-v0.12.6`, exposed by `/usr/local/bin/nvim`; verified the download against its GitHub release asset SHA256. Updated Nexus `~/.config/nvim/init.lua` to route dashboard terminal pastes into a new editable buffer. Updated `lua/smart_quit.lua` to refuse ordinary quit of an unsaved last buffer and to quit Neovim without explicitly killing a tmux window. Restarted only the idle dashboard after RPC confirmed no modified buffers. Live RPC confirmed v0.12.6, Telescope command registered, mouse capture off, and empty startup messages.

Hermes logs showed a ChatGPT-account entitlement rejection for `gpt-5.5`, a resulting year-long model block that also prevented auxiliary credential selection, and a separate expired access token. Refreshed the existing `openai-codex` OAuth credential with the supported CLI, reset its saved status, and replaced configured main/auxiliary `gpt-5.5` references with `gpt-6-sol` in root plus nexus/tensor/qubit profile configs. Replaced startup-warning MCP toolset selections `mcp-unifi` / `mcp-prometheus` with supported bare aliases `unifi` / `prometheus` in those same four files. Credentials remain in their existing private store. Operational checks: config toolset validation passed; a live auxiliary request returned OK; MCP discovery exposed two UniFi and four Prometheus tools. Discovery cleanup stopped only the temporary MCP children created by this check. Running Hermes chats/container were preserved; new chats load corrected defaults.

Pending limitation: prior web_extract calls fail because no extraction provider is configured; existing Codex native search cannot extract page contents. No provider was added. Earlier failed shell commands in agent logs are historical tool invocations, not evidence of current service failure. No formal tests or backups were created.

Rollback references: remove `/usr/local/bin/nvim` to return to Debian `/usr/bin/nvim`; the new official release lives only in `/opt/neovim-v0.12.6`. The dashboard paste change is the appended `original_paste` wrapper in `init.lua`; the safe-quit guards are in `lua/smart_quit.lua`. Hermes prior main/auxiliary model was `gpt-5.5` (rejected by this account), and prior MCP selections were `mcp-unifi` / `mcp-prometheus`; restoring those settings would restore the observed failures. OAuth refresh rotates the existing login; do not restore old token copies.

## 2026-10-15 — One Nexus Hermes runtime from every host

Updated canonical `tools/hermes-homelab` and installed copies on Qubit, Tensor and Nexus. All three now provide `~/.local/bin/hermes`, selecting the caller's existing profile. Clients SSH to Nexus and call absolute `/usr/local/bin/hermes`; Nexus invokes that Docker backend directly. This avoids launcher recursion, preserves separate profiles, forwards top-level CLI flags, and allocates a remote TTY only for interactive terminals. Remote SSH selects the existing `nexus` alias/key even when overriding its address for the fallback, with strict host checking. Added an idempotent local-bin PATH entry to each host's `.zshenv` so SSH command shells also find the command. Updated installer host selection and README. Existing Hermes sessions and private state preserved; no service restart or backups.

Verified `hermes --version` from Tensor, Qubit and Nexus: all reported `/opt/hermes`, Docker install v0.21.6. LAN routing works. A separate Tailscale-address SSH check encountered Tailscale SSH's interactive authorization gate and was cancelled; outside-LAN access is pending that authorization. No Tailscale settings were changed.

Rollback: remove Nexus `~/.local/bin/hermes` to expose the original `/usr/local/bin/hermes` behavior; remove the marked PATH stanza from `.zshenv` if no longer wanted. Client commands still route exclusively to Nexus; original private credentials remain in their existing stores. Prior launcher source is described in the 2026-10-14 source record; no duplicate backup files were created.

## 2026-10-15 — tmux Hermes window uses the central launcher

Updated canonical and installed `tmux-ensure-layout` on Qubit, Tensor and Nexus so managed window 3 executes the absolute user `~/.local/bin/hermes` launcher. New windows carry `@homelab-hermes-launcher=nexus-central-v2`; layout repair preserves a matching window and moves an older/unmarked one to a free index >=10 before starting the current launcher. Added explicit Homebrew/system tmux discovery for noninteractive Qubit shells and safe handling of missing window markers. Existing bootstrap and after-new-session hooks already call this helper, so future sessions use the same entry.

Applied to Qubit/Tensor `main` and Nexus `nexus`. Previous Hermes sessions remain alive in Qubit/Tensor window 10 and Nexus window 11, named `previous-hermes`. Nexus window 4 and all unrelated applications were preserved. Active window identity was preserved. All three new window-3 panes displayed `gpt-6-sol`, carried the new launcher marker and showed no credential/unknown-tool/traceback/connection/trust startup errors in the visible pane. No formal tests, backups or service restarts.

Rollback: close only the newly created window 3 after saving any new work, then move that host's preserved `previous-hermes` window back to index 3. To prevent layout repair from moving it again, either revert the helper's window-3 command to `~/.local/bin/hermes-homelab` and remove the revision check, or mark the preserved window with the current launcher revision after confirming its session is the desired one. These are tmux layout/launcher changes; private Hermes state remains on Nexus.


## 2026-10-15 — SSH from Hermes

All host profiles run in Nexus Docker and share /opt/data/.ssh/config. Use `ssh qubit` (wired 192.168.1.4), `ssh qubit-wifi` (192.168.1.102) or `ssh tensor` (192.168.1.3), as iragonforce. Strict host-key verification and a dedicated source-restricted key are configured. Both target machines were reached through the actual Hermes terminal tool in each profile. Do not assume qubit automatically falls back between interfaces. This is verified LAN access, not off-site SSH validation. For rollback see the kit audit/HERMES-SSH-2026-10-15.md.


## 2026-10-15 — Copy feedback parity check

Qubit and Tensor both have native Ghostty mouse selection and Super+C/Command+C copy with tmux mouse off, plus matching 3-second bottom-line character/line feedback from client-local helpers. Both local tmux `main` sessions are attached. A stdin-only Unicode preview returned and delivered identical `12 characters, 3 lines` messages to tmux on both hosts without reading or changing clipboard text. Actual mouse/key copy remains user-verifiable. This is a helper-based tmux feature, not a claim of native macOS Ghostty toast support. See the kit CHANGELOG matching-feedback entry for scope and rollback.


## 2026-10-15 — Superseding clipboard behavior

Qubit/Tensor now use tmux mouse ON, explicit copy-pipe helpers, private Ghostty copy/paste keys, and a transient four-second bottom copy-count message only. Clipboard watchers are disabled. Qubit actual key-byte and clipboard roundtrip verified using a disposable PTY with clipboard representations restored from memory. See kit CHANGELOG for full scope, the CSI extended-key parsing fix, rollback, and pending physical confirmation. Earlier mouse-off/helper-watcher notes are historical.

2026-10-15 follow-up: user confirmed copy works; copy-count message now centered and transient for one second on Qubit/Tensor (supersedes the previous four-second setting). Both render/expiry paths checked with attached PTYs.

2026-10-15 correction: latest user-selected copy indicator duration is TWO seconds (2000 ms), still centered and transient, on Qubit/Tensor. This supersedes the one-second setting.

2026-10-15 copy UI follow-up: centered two-second message retains yellow only behind text; message-style no longer has full-line fill, preserving surrounding status fields. Rendering/expiry verified on Qubit and Tensor.

## 2026-10-16 — Qubit WhatCable duplicate startup

After reboot, observed two processes: `/Applications/WhatCable.app/Contents/MacOS/WhatCable` from user LaunchAgent `~/Library/LaunchAgents/com.user.whatcable.plist` (RunAtLoad/KeepAlive), and `/Applications/WhatCable.app.backup/Contents/MacOS/WhatCable` from macOS's generated application launch job. The System Events login item named WhatCable pointed to `/Applications/WhatCable.app`, but launch registration resolved its second process to the backup bundle. Removed only the WhatCable login item and sent TERM only to the backup process. Readback showed one main-app process, the LaunchAgent running, and no WhatCable login item. No reboot verification yet. Rollback: `osascript -e 'tell application "System Events" to make login item at end with properties {name:"WhatCable", path:"/Applications/WhatCable.app", hidden:false}'`; this would restore the duplicate startup path unless the LaunchAgent is also disabled. The backup app bundle was not altered.

## 2026-10-17 — Qubit native SSH LAN-first/Tailscale fallback

Diagnosed Qubit Wi-Fi LAN SSH timeout: current Wi-Fi address 192.168.1.154 is absent from Nexus's narrow SSH source allowlist; captured six SYNs and corresponding host-guard drops. UniFi read-only client inventory confirmed the address/MAC. After user connected Ethernet, Qubit obtained 192.168.1.4 and direct LAN SSH succeeded. No UniFi, DHCP, firewall, server, Tailscale, trust-store, key or agent changes were made.

Installed client-only routing: ~/.ssh/config now includes ~/.ssh/homelab-routing.conf first; ~/.local/bin/homelab-ssh-connect retains the successful TCP socket, trying LAN for two seconds then Tailscale for five. `ssh nexus` and `ssh tensor` use that helper; explicit `nexus-lan`, `nexus-ts`, `tensor-lan`, `tensor-ts` aliases are available. Strict host-key checking uses the existing trusted LAN host identities across transports. Authentication/host-key/remote-command failures do not trigger retries. A TCP connection that opens but stalls before its SSH banner is bounded by OpenSSH's 12-second ConnectTimeout, not retried via Tailscale. Existing unrelated SSH configuration remains intact; Bitwarden is deferred.

Operational checks from Qubit: automatic Nexus LAN 0.16s, direct LAN 0.14s, direct Tailscale 0.11s, actual Wi-Fi-source LAN timeout followed by Tailscale success 2.16s; SFTP pwd/quit succeeded. Tensor was offline: helper attempted both addresses and failed in 7.07s. All six aliases parsed with strict checking and intended endpoints; deployed file hashes/permissions were read back. Actual external-network behavior, Tensor authentication/host identity, Ethernet reconnect/reboot behavior and Wi-Fi reservation repair remain pending. No formal tests were added or run.

Rollback: Qubit /Users/iragonforce/.local/state/ssh-routing/20261017-005058/config.before and ROLLBACK.txt. Restore config.before to ~/.ssh/config with mode 600, then remove only ~/.ssh/homelab-routing.conf and ~/.local/bin/homelab-ssh-connect. No service restart or existing-session termination is needed. Canonical kit source and this Hermes context are updated; full mirror sync is deferred while Tensor is down, avoiding tmux reloads or unrelated work.
## 2026-10-17 — SSH mesh verification

All three hosts reached Qubit, Tensor and Nexus using both the LAN aliases (`ssh qubit`, `ssh tensor`, `ssh nexus`) and explicit Tailscale aliases (`-ts`). Nexus Tailscale SSH was disabled; regular sshd and existing keys now handle its 100.x SSH traffic without the Tailscale browser check. Tensor's Qubit alias uses wired 192.168.1.4 because current split DNS returned stale 192.168.1.102. See `sources/SSH-MESH-2026-10-17.md` for the matrix, trust checks, backups and rollback. Offsite access was not separately exercised.


## 2026-10-26 — SSH access repair

Qubit, Tensor and Nexus now complete all nine short-name `ssh qubit` / `ssh tensor` / `ssh nexus` connections as `iragonforce` in a live batch check. The key contents were not changed. The repair corrected truncated and macOS-only ProxyCommand paths copied into Linux SSH configs, set the three homelab private keys on each Linux host to mode 0600, and added two Nexus known-host entries only after matching their presented ED25519 keys to Qubit's existing trust. Strict host-key checking remains enabled. This is current-path verification, not forced Tailscale fallback or offsite verification. See the 2026-10-26 kit CHANGELOG entry; config rollback copies are at `~/.local/state/ssh-repair-20261026/config.before` on each host.
