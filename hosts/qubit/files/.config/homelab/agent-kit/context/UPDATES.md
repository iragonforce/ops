# Append-only context updates

## 2026-10-15 — skill inventory correction

Read-only live audit found that each named Hermes profile now contains two different skills declaring hermes-agent: the original root-level directory and `autonomous-ai-agents/hermes-agent`. Bare-name resolution is ambiguous; use the nested path until consolidation is requested. There are six files but five loadable entries per named profile; default remains five unique files. `/skill plan` invokes the planning skill because `/plan` is reserved. Reference library remains 623 entries. No skills/configuration changed. See parent `audit/HERMES-SKILLS-2026-10-15.md` for evidence limits.

## 2026-10-14 — initial handoff

Created topic-based context from the visible user requests and dated local implementation notes. Collected selected live Nexus container/network/mount/export/pool metadata. Existing Hermes v0.21.6 is running healthy. Bulk and fast report ONLINE; OTBR is stopped, which differs from the older IoT record. No provider login, inference request, external message or service restart was performed to create the context pack.

This pack preserves the current distinction between prepared graphics changes and a validated physical repair. MX Master configuration is complete at the software/device-settings level; gesture response awaits the user's confirmation.

Future entries should include timestamp/timezone, current request, changed paths/services, before/after state, validation performed, rollback references and remaining uncertainty. Correct topic summaries as facts change; do not edit historical source notes to make them appear current.

## 2026-10-14 — Nexus terminal text selection

User requested selectable text through Nexus tmux/Neovim. Disabled tmux mouse capture in `~/.tmux.conf` and the running server, and added `vim.opt.mouse = ""` to Neovim init. No editor was running. Backups: `~/.local/state/terminal-selection/20261014-210228/`. Normal terminal drag and local Copy shortcut are intended; physical clipboard interaction is user-side. Existing clipboard settings and SSH/tmux sessions were retained. The live context pack was updated; the initial bulk recovery pack remains the original handoff snapshot.

## 2026-10-14 — shared agent kit and terminals

Audited selected Codex/Claude settings on all three hosts, unified global instructions and built a 623-entry deduplicated skill-reference library. Five skills are active in Hermes. Qubit is the canonical kit host; Tensor/Nexus carry mirrors. Hermes runs centrally in Nexus Docker with separate nexus/tensor/qubit profiles. Native tools, the Home Assistant plugin and two verified read-only stdio MCP servers replace eleven dead MCP connections. Provider credentials and vendor client settings remain private and unchanged. Supported optional dependency synchronization fixed real CLI MCP discovery. Added narrowly scoped router/Home Assistant firewall exceptions for Hermes.

All required tmux applications are running at 1 zsh, 2 nvim, 3 hermes, 8 superfile and 9 btop on each host. Conflicting apps were moved to higher indices. Fixed Qubit's corrupt active Superfile TOML and the version-dependent btop flag. Normal terminal selection remains enabled through mouse capture off. See parent CHANGELOG.md for checks and ROLLBACK.md for per-host backups, Hermes recovery and firewall IDs. No model inference or external messages were sent; physical display and off-site access remain unverified.

## 2026-10-14 — user requested commands without approval prompts

Set Hermes `approvals.mode: "off"` for the root runtime and all three host profiles through its supported CLI. Before-state configs are stored privately under `/opt/data/recovery/approvals-20261014-220107`. No custom deny rules were present. The framework's immutable hard blocks and OS permissions remain applicable. See parent CHANGELOG.md for exact rollback commands. This changes command approval behavior, not historical task authorization.


## 2026-10-15 — verified Hermes SSH access

Nexus host SSH to Qubit and Tensor was already working. Hermes lacked keys/aliases and network access. Added a dedicated persistent Hermes key, source-restricted target authorized_keys entries, verified host keys, and exact UniFi TCP22 exception 7962bda8-ae24-4ddf-b3ef-8152c85480b7. Actual Hermes terminal-tool calls in all three profiles reached both hosts as iragonforce with exit code 0. The alternate Qubit Wi-Fi alias also connected successfully. No model inference or service restart was used. See audit/HERMES-SSH-2026-10-15.md in the kit for recovery paths and rollback. Existing skills were not changed.


## 2026-10-17 — Paperclip Hermes gateway prepared; registration pending

Prepared Hermes Gateway agent form in existing Paperclip homelab organization. Added private loopback relay 127.0.0.1:18642 using the existing paperclip-hermes Docker bridge; installed adapter connection check passes and relay is healthy. No Paperclip/Hermes restart, model inference or task work was started. Final API-key secret storage and agent creation remain pending action-time browser confirmation. See audit/PAPERCLIP-HERMES-2026-10-17.md for details and rollback.


## 2026-10-17 — Hermes registered in Paperclip; private HTTPS enabled

After explicit approval, created the encrypted Hermes Gateway API organization secret and the Hermes Gateway agent (ea829891-5ec7-4080-999f-1966317644da); approved its hire. Stored callback http://paperclip:3100 and current-homelab instructions. Periodic heartbeat remains off; agent was idle with no runs. Used named-secret workflow to avoid the automatic secret-naming crypto.randomUUID browser error. Configured private Tailscale HTTPS at https://nexus.tail4e4f0f.ts.net:9443, exact host allowlist and public URL. Briefly recreated only idle Paperclip and its relay; Hermes was not restarted. Verified valid TLS/app and health HTTP200, callback reachability and adapter pass after restart. New HTTPS origin requires sign-in; no authenticated HTTPS login or model run was performed. Cloudflare Access redirects exist for nexus/paperclip.blinkwired.com, but no matching NPM app routes were found; public application routing remains pending. See audit/PAPERCLIP-HERMES-2026-10-17.md for IDs and recovery paths.


## 2026-10-17 — Paperclip runner API and separate Tensor Ollama agent

- Corrected `PAPERCLIP_API_URL` to `http://paperclip:3100` in Nexus `/srv/containers/compose/paperclip/compose.yaml`. Docker runners could not reach the browser Tailscale URL. Browser `PAPERCLIP_PUBLIC_URL` remains `https://nexus.tail4e4f0f.ts.net:9443`. Recreated idle Paperclip and its loopback Hermes relay only.
- Created and approved **Tensor Ollama**, ID `0e56606c-6ecf-4047-8fd7-e6eee1b3ca09`, using `opencode_local`, model `ollama_tensor/gpt-oss:20b-64k`, existing Tensor Ollama endpoint, and persistent runner workspace `/paperclip/workspaces/tensor-ollama` (host `/srv/containers/data/paperclip/workspaces/tensor-ollama`). Reports to coordinator. Timer heartbeat off, on-demand wake on; agent/skill creation permissions off.
- Hermes remains on its existing Codex configuration; its adapter configuration fingerprint was unchanged. No Tensor installation, model download or inference was performed in this maintenance step.
- Used the installed application's board-auth service to issue a five-minute maintenance credential for the existing administrator, then submitted the hire/approval through normal REST APIs. Credential stayed in process memory and was revoked in finally; revocation independently verified. Coordinator privileges and authentication mode were unchanged.
- Operational checks: internal API health HTTP 200; normal authenticated hire and approval succeeded; Tensor model catalog reachable from Paperclip; OpenCode recognizes the exact configured provider/model; workspace owned by UID 1000; agent idle. First actual Paperclip inference task and subsequent wake remain pending. An initial direct OpenCode probe incorrectly passed normalized environment objects; rerunning with their plain values succeeded, requiring no configuration change.
- Rollback before changes: `/srv/containers/data/paperclip/recovery/runner-api-20261017-191804` contains prior Compose configuration. `/srv/containers/data/paperclip/recovery/tensor-ollama-20261017` contains prior agent records, hire payload/result, verification and rollback notes. Pause the new agent before rollback and check for assigned work; preserve audit history and workspace.
- Existing public custom-domain routing remains pending. Private board URL: https://nexus.tail4e4f0f.ts.net:9443 .


## 2026-10-17 — Paperclip UI instruction editing

- Confirmed the existing user account already has `instance_admin`; no privileges or authentication settings were changed.
- Migrated Tensor Ollama's external host instructions and Hermes's inline instructions into managed Paperclip bundles through supported board APIs. Coordinator was already managed and retained its content. All three now use managed instructions.
- Preserved original entry content, external source files and existing instruction candidates. Seeded Hermes's managed entry from its original inline instructions because the generic bundle exporter does not read that adapter's inline `instructions` field.
- Verified managed revision commits and read-back content equality for Hermes and Tensor Ollama. Models, provider credentials, networks and services were not changed or restarted. UI-only/browser rendering was not rechecked; copy unsaved editor text before reloading, then retry saving. Existing drafts/candidates were not automatically applied.
- Used short-lived local maintenance credentials for the existing admin, revoked in finally on every attempt. Initial probes stopped on revision-token shape and external candidate-list restrictions; the final normal commit used the current revision ID and succeeded.
- Private backup, prior configuration, original entry copies, candidate records and rollback: Nexus `/srv/containers/data/paperclip/recovery/managed-instructions-20261017`. Restore prior instruction config fields through the board API only after checking current edits/runs; retain managed revision history.
- Instance-admin access covers supported Paperclip UI settings. Host OS/Docker configuration and fields not exposed by Paperclip still require host administration.


## 2026-10-17 — Paperclip knowledge migration, MCP and linked records

Imported 1,146 packages from available Qubit/Tensor/Nexus skill sources (1,115 distinct original documents plus focused/nested skills). Preserved checksummed raw archives, consistent Hermes database snapshots, and 101,524 searchable redacted history chunks; four malformed lines remain archive-only exceptions. Added reviewed UniFi/Prometheus, bounded local knowledge/Obsidian, and official Context7 connections, with 12 reviewed tools assigned to the three agents. Retained existing connections and models. Scoped broker calls for history, Context7, UniFi, Prometheus and a note write/sync succeeded. Installed focused Hermes compatibility skills because its gateway lacks file sync. Added 126 linked Obsidian notes in secondBrain/Homelab/Paperclip and verified current note synchronization. No shortcut was created/imported per user correction; manual recipe and the working paperclip-request status helper are prepared. Telegram connectors enabled but dedicated token/public webhook/pairing still pending. Rollback: /srv/containers/data/paperclip/recovery/knowledge-20261017. See context/21-paperclip-knowledge.md and audit/PAPERCLIP-KNOWLEDGE-2026-10-17.md.

## 2026-10-17 — Paperclip skills corrected; existing Telegram bot connected

- Reduced active company skill library from 1,154 to 11: removed 1,143 unused imported references through supported API. All original source packages and private imports remain; three focused local skills reviewed, eight vendor bundles retained. Full inventory screening is not exhaustive script security certification.
- Reused Nexus telegram/runtime.env credential for @iragonforce_bot through encrypted native Paperclip setup. Inbound ownership moved from old OpenClaw polling relay to Paperclip; outbound notification REST endpoint retained. Direct messages only; unlinked users blocked.
- Narrow public Telegram webhook via Cloudflare; unsigned actual endpoint rejected 401, UI Access retained. Pending real owner message, identity link and native conversation qualification.
- Rollback: Nexus /srv/containers/data/paperclip/recovery/telegram-paperclip-20261017; Qubit ~/.local/state/paperclip-integration/telegram-20261017. Remove webhook before restoring old polling.
- Details: audit/PAPERCLIP-CURATION-TELEGRAM-2026-10-17.md and context/21-paperclip-knowledge.md.

### 2026-10-18 final knowledge check

Granted UID 10000 read/traverse only at the staged public root after saving its ACL. Refreshed the knowledge catalog/health. Paperclip broker record_change saved the linked curation/Telegram note and synchronized it to Qubit. Real Telegram owner message/link remains pending.

## 2026-10-18 — Paperclip connection identities repaired

Revoked empty duplicate shared identities for Knowledge, UniFi and Prometheus; preserved working default credentials. Added coordinator/Hermes/Tensor installation targets for four migrated connections alongside existing tool profiles. Fixed read ACL only on staged history.sqlite, refreshed catalog/health. Native resolver selected all four expected coordinator connections; broker history_search succeeded. No restarts or credential changes. Rollback: Nexus /srv/containers/data/paperclip/recovery/identity-20261018. Details: audit/PAPERCLIP-IDENTITIES-2026-10-18.md.

## 2026-10-18 — Nexus node full sudo explicitly authorized

Installed root-owned 0440 /etc/sudoers.d/90-node-admin granting node ALL=(ALL:ALL) NOPASSWD: ALL at the user’s explicit request. Preserved existing keys, aliases, limited Hermes rules and Docker socket permissions. Complete sudoers validated; node sudo -n id -u returned 0 and sudo -n docker info succeeded. Rollback /var/backups/homelab/node-sudo-20261018. Details audit/NEXUS-NODE-SUDO-2026-10-18.md. No service restart or password change.

## 2026-10-18 — Tensor standby lighting uses native OpenLinkHub

Replaced SDK takeover/Direct bridge writes with native hub Off on standby and original native awake hub profiles on wake, plus OpenRGB Default for RAM/GPU/motherboard. Preserved protected AIO curves and existing Off temperature ramp. Rebased stale Default profile identities/LED counts, preserving selected effects/palette. Added SDK service availability check to hibernate wrapper; started existing OpenRGB/checkpoint services. Lighting-only cycle passed; no monitor cycle, desktop restart, suspend/reboot or formal tests. Rollback Tensor ~/.local/state/tensor-control/recovery/standby-olh-20261018 and /var/backups/homelab/tensor-standby-olh-20261018. Details context/sources/TENSOR-STANDBY-LIGHTING-2026-10-18.md.

## 2026-10-18 — Tensor ten-minute idle and faster Bluetooth connection mode

Verified existing hypridle timeout 600 → hibernate, restarted only its user service. Enabled supported FastConnectable live and persisted it in /etc/bluetooth/main.conf without restarting Bluetooth or changing device records. No continuous scanning job. Actual idle wait/reconnect latency remains physically unmeasured. Rollback /var/backups/homelab/bluetooth-fast-connect-20261018. Details context/sources/TENSOR-IDLE-BLUETOOTH-2026-10-18.md.

## 2026-10-19 — Read-only Nexus media VPN audit

Confirmed actual namespace egress via Swiss PIA for Prowlarr, Radarr, Sonarr, Lidarr, Bazarr, Cleanuparr, qBittorrent and FlareSolverr on VLAN 2. Seerr and Jellyfin remain on VLAN 5 with regular Canadian WAN egress. UDR7 guard active, first IPv4/IPv6 jumps and marked VPN routing verified. No outage exercise, service restart or network/container configuration change. Details context/sources/NEXUS-MEDIA-VPN-AUDIT-2026-10-19.md. Exceptions require a future migration request; no system rollback needed.

## 2026-10-23 — HOM-18 workspace repair and restart

Paperclip blocked HOM-18 before `codex_local` launch because the Homelab Knowledge primary workspace was the non-Git migrated corpus `/paperclip/migrations/20261017/public`. Preserved it as a secondary workspace, created `/paperclip/workspaces/homelab-knowledge` as a dedicated Git checkout, and updated the primary workspace and failed execution-workspace cwd. Cleared the coordinator error after confirming zero live runs and resolved the recovery action. The authorized retry and two Paperclip-generated continuations all ended `succeeded` with advanced liveness. Final state is `in_progress`/`waiting_for_answer`; the coordinator is idle with no live runs. The final handoff asks Sergey to confirm agent/runtime priorities, permission boundaries, and reporting hierarchy before setup resumes. No agents were created and no Obsidian deliverable was verified. Rollback: `/srv/containers/data/paperclip/recovery/hom18-workspace-repair-20261023/rollback.txt` (mode 0600).

## 2026-10-23 — coordinator board access

Granted `canAssignTasks=true` to Paperclip coordinator through the supported agent-permissions API, preserving its existing `canCreateAgents=true` and `canCreateSkills=true`. The built-in `paperclip-board` skill was already desired/configured and will link into the runtime on its next run. Readback verified all three permission flags, coordinator idle, and zero live runs. No new connection, credential, skill, issue, task, or agent was added or started. Rollback: Nexus `/srv/containers/data/paperclip/recovery/coordinator-board-access-20261023/rollback.txt` (mode 0600).

## 2026-10-23 — coordinator approval bypass for `record_change`

At the user's request, removed the coordinator-only Paperclip `require_approval` policy for the Homelab Knowledge `record_change` tool. The tool profile already explicitly included the catalog entry; no new tool access, connection, credentials, or broad profile was added. The pre-change policy test returned `require_approval`; post-change returned `allow` / `allowed=true`. The coordinator's saved `codex_local` config already had `dangerouslyBypassApprovalsAndSandbox=true`; that setting was not changed. The other agent's approval policy remains intact. No run or tool invocation was started. The connection currently reports `error` (`connect ECONNREFUSED 172.18.0.3:8768`), so real execution and Obsidian/Qubit sync remain pending. Rollback: `/srv/containers/data/paperclip/recovery/coordinator-record-change-approval-20261023/rollback.txt` (mode 0600). Direct PATCH and a temporary allow override failed to change effective policy; the temporary rule was deleted before removing the exact scoped approval rule.
