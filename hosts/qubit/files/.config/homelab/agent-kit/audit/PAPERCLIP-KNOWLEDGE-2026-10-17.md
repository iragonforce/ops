# Paperclip knowledge migration — 2026-10-17

## Scope and source coverage

Collected available local Codex/Claude/OpenClaw skill packages, agent-kit records, memory and session logs from Qubit, Tensor and Nexus. Also captured consistent SQLite snapshots and message exports from Nexus's Hermes root and named profiles. Authentication stores such as SSH private keys and provider login files were excluded from the searchable import. Credential-bearing configuration references and original transcripts are kept only in private archives.

| Source | Captured files | Skill locations |
|---|---:|---:|
| Qubit | 5,275 | 2,094 |
| Nexus host | 1,121 | 674 |
| Tensor | 3,281 | 1,779 |
| Nexus / Hermes | 236 | 40 |

- 1,115 distinct source skill documents were preserved, with resource variants and provenance. Three focused local skills were added. Paperclip imported 1,146 packages including nested skill packages, with no import warnings.
- The history index contains 101,524 deduplicated text chunks and 176,389 source occurrences.
- Four malformed JSON lines in two historical Claude copies remain in their original archives and are excluded from search. See `history-exceptions.json` for source paths and line numbers.
- All four archive checksums were verified again on Nexus after transfer.
- The capture is a point-in-time import of available local sources, not a claim that every cloud-only conversation or deleted session was recovered.

## Storage and UI

- Paperclip project: **Homelab Knowledge**, with a registered local workspace.
- Host workspace: `/srv/containers/data/paperclip/migrations/20261017/public`.
- Container workspace: `/paperclip/migrations/20261017/public`.
- Original archives and manifests: `/srv/containers/data/paperclip/migrations/20261017/private/archives` (private directory, archives mode 0600).
- Search index: workspace `history.sqlite`, read as an immutable snapshot. It contains user, assistant, tool and memory records; hidden reasoning fields were excluded.
- A temporary in-memory scan of known credential values plus token/private-key patterns applied redactions. This is best effort, not a guarantee that every historical secret was detected. Do not publish archives or bulk transcript exports.
- Imported skills are reference material. Only the three focused homelab skills were newly assigned; old tasks are not reactivated by the import.

## MCP connections and trust decisions

| Added connection | Source / purpose | Newly discovered tools |
|---|---|---:|
| UniFi Homelab | Existing local read-only wrapper, retaining TLS fingerprint validation | 2 |
| Prometheus Homelab | Existing local read-only monitoring wrapper | 4 |
| Homelab Knowledge | Reviewed local code for bounded history retrieval and linked Obsidian records | 4 |
| Context7 Official | Upstash's official remote documentation MCP | 2 |

The explicit **Homelab tools and knowledge** profile includes these 12 catalog entries and is bound to all three current agents. Existing application connections and profiles were retained. Their effective tool lists also contain pre-existing tools.

No MCP process was found running on Tensor during inspection. Its installed skill/config references were still captured. Qubit's app-only computer-use capabilities were preserved as references rather than treated as portable Linux services.

The new `paperclip-knowledge` service reuses the installed pinned Hermes image and the already installed MCP Python SDK. It shares Hermes's network namespace, binds only loopback and the private Paperclip bridge, requires a bearer credential, runs as UID 10000 with dropped capabilities/read-only root/bounded logs, and has no Docker socket. The existing Hermes process was not restarted. Credential values are private; the UI holds an encrypted secret reference.

Connections use Docker DNS for persistence. The service discovers its private bridge interface within the configured CIDR; it never binds the LAN/VLAN address. Health checks use loopback.

## Token-saving choices

- Retrieve a few history hits and bounded excerpts instead of replaying full sessions.
- Deduplicate skill documents and preserve provenance/resource variants.
- Assign a small task-relevant skill set instead of injecting every migrated skill.
- Reuse native shell, filesystem, SSH and Docker tools rather than adding redundant MCP wrappers.
- Use Context7 for narrow public library-documentation queries; never send private host configuration to it.
- Keep the existing client context-mode plugin available where supported. No additional broad code-execution MCP service was deployed merely to duplicate native processing.
- No numerical claim of measured token savings is made.

Research references:

- [Paperclip skills and local import](https://docs.paperclip.ing/reference/skills/)
- [Paperclip tool gateway](https://docs.paperclip.ing/reference/api/tool-gateway/)
- [Context7 security and data handling](https://context7.com/docs/security/overview)
- [Context-mode upstream design](https://github.com/mksglu/context-mode)

## Agent skills and instructions

Added **homelab-history**, **homelab-change-journal** and **homelab-token-efficiency**. Coordinator and Tensor Ollama use supported Paperclip skill synchronization. Hermes gateway records assignments but does not implement skill synchronization, so three focused native copies were installed under its root and shared qubit profile. Existing native skills were retained.

All three managed instruction bundles received a short section on retrieving history, using the reviewed tool profile, and recording actual completed work. Edits used the current revision token and preserved existing instructions. Providers/models, existing credentials and account permissions were not changed.

## Obsidian

- Vault section: Qubit `~/Library/Mobile Documents/iCloud~md~obsidian/Documents/secondBrain/Homelab/Paperclip`.
- The section currently has 126 Markdown notes, including host/service pages, copied dated handoffs, change notes and a graph entry point at `Home.md`.
- `record_change` creates linked notes on Nexus and pushes the note plus the Changes index to Qubit using existing SSH credentials and a path-restricted import helper.
- A real migration change record was successfully created and synchronized to Qubit.
- If Qubit is offline, the note remains on Nexus and the tool reports sync pending. No recurring synchronization job was created.
- Existing inherited ACLs required a narrowly scoped UID 10000 write entry on the staged Obsidian subtree; prior ACLs are saved for rollback. Existing pool trees and other vault content were not recursively changed.

## Siri and Telegram

- No Siri shortcut was created or imported, per the user's correction. See `PAPERCLIP-SIRI-COMPOSE.md` for exact manual composition steps.
- Installed `~/.local/bin/paperclip-request` on Qubit and the bounded Nexus-side helper. The status branch works through existing SSH; task submission and voice invocation have not been exercised.
- Enabled Paperclip's native chat-connectors setting. Telegram remains pending a dedicated bot token at Qubit `~/.config/homelab/paperclip-telegram-token` and the public HTTPS webhook setup. Existing Telegram bots were left intact.
- The [official Telegram connector](https://docs.paperclip.ing/connectors/telegram/) requires a public HTTPS webhook and recommends a dedicated bot. Current private Tailscale HTTPS on port 9443 is not a Telegram webhook endpoint.

## Checks, rollback and pending work

Verified archive checksums, skill import results, assigned profiles, history search, note reading, actual UniFi overview/Prometheus target queries, Obsidian writing and Qubit synchronization, and the CLI status path. History retrieval, a public Context7 library lookup, UniFi overview, Prometheus targets and a linked note write/sync also succeeded through Paperclip's broker with the coordinator's scoped access. The broker allowed these calls without requiring a new agent inference run. No formal test suite or new model inference run was performed.

Operational checks found and corrected the draft connection state, missing organization credential-grant mappings, inherited staged-note ACLs, immutable SQLite read access, and an inefficient history join. The final search uses document/host indexes and a bounded ranked query; a direct database lookup returned two results in 0.002 seconds. This is not a token-savings measurement. The local HTTP bridge also handles chunked requests, with protocol-only bounded logging and no request arguments or headers in its logs.

Private rollback: `/srv/containers/data/paperclip/recovery/knowledge-20261017`. It contains the prior Hermes Compose YAML, instruction snapshots and original Obsidian ACLs. Disable the added connections before stopping only `paperclip-knowledge`; restore prior Compose/ACLs only after checking later edits. Keep source archives, native data and imported revisions until cleanup is explicitly requested. Temporary maintenance board credentials were revoked in finally; the CLI likewise revokes its one-minute credential.

Pending: Telegram credentials/webhook/user pairing, a user-composed Siri shortcut and voice invocation, and an actual new agent run exercising the imported runtime knowledge. Malformed historical lines remain an explicit archive-only exception.
