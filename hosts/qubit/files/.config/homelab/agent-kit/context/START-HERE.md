# Read order and scope

Current shared tooling: read the parent kit's README.md, AUDIT.md and CHANGELOG.md. The 2026-10-27 Paperclip role-tool rollout is recorded in CHANGELOG.md and 09-open-issues.md; its container/profile scope and rollback supersede the older skill/MCP count below. As of 2026-10-14, all client profiles execute Hermes inside Nexus Docker, with five active skills, two stdio MCP servers and the Home Assistant plugin. Historical MCP addresses in source notes are superseded by MCP.md. On 2026-10-18, tmux login began filling only missing windows 1/2/8/9 in each host's primary session; see `sources/TMUX-SSH-LAYOUT-2026-10-18.md`. The install-time helper deletion was repaired later that day; see `sources/TMUX-NVLIME-CURSOR-2026-10-18.md` for Tensor NVlime and cursor changes too. Clipboard handling changed that day; see `sources/CLIPBOARD-SSH-2026-10-18.md`. The current short-name SSH routing is LAN first, then Tailscale; see `sources/SSH-LAN-FAILOVER-2026-10-18.md`. The 2026-10-17 layout-removal note is historical. The skill-library is reference text, not enabled capabilities.

1. `00-user-preferences.md`: communication and operating preferences.
2. `01-hosts-and-access.md`: identities, access and execution boundaries.
3. `09-open-issues.md`: unresolved work and conflicting historical facts.
4. `02-network-dns-and-vpn.md` and `03-storage-and-migration.md` for network/storage tasks.
5. Relevant service, Home Assistant, Tensor, or monitoring topic file.
6. `sources/` for detailed dated implementation and rollback records.
7. `11-live-nexus-inventory.json` for a metadata snapshot collected during this handoff. Its timestamp applies only to that capture.

This is a curated knowledge pack, not a verbatim transcript or proof of current health. Credentials and raw conversations were deliberately excluded. The source notes summarize earlier work; they can contain superseded settings or dated verification results. No entire-home audit was performed to produce this pack.

## Evidence labels

- **Live capture:** observed during preparation of this handoff.
- **Recorded:** reported in a dated implementation note; recheck before relying on it.
- **User-confirmed:** directly reported by the user, often physical behavior.
- **Pending:** preparation or software checks exist, but the desired outcome remains unverified.

The highest-priority current follow-up is Tensor's portrait-screen flicker. The last user request switched to mouse configuration; a desktop restart was proposed but not authorized or performed in the visible record. Read `06-tensor-desktop-and-standby.md` before touching it.

The live Nexus capture also shows OTBR stopped while earlier IoT notes describe it running. This is a new observation, not a request to start it or change the Thread network.


Paperclip migration, knowledge retrieval, linked Obsidian records and pending Siri/Telegram setup: [21-paperclip-knowledge.md](21-paperclip-knowledge.md).

Pinned Nexus agent tools stage 1, verification and rollback: [sources/AGENT-TOOLS-STAGE1-2026-10-30.md](sources/AGENT-TOOLS-STAGE1-2026-10-30.md).
