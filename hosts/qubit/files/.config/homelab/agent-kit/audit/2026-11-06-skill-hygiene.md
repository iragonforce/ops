# Agent skill usage — 2026-11-06

On-demand collection only. Run `python3 ~/.local/bin/skill-usage` on any host. On Nexus this also refreshes Hermes records. Source logs, session databases and prompts stay local; reports contain skill names and aggregate counters.

## Current libraries

Nexus Hermes and the three Codex user libraries have 14 skills. Codex system and installed-plugin skills remain separate. Tensor local Hermes remains independent.

agent-tools-stage1, docx, github, google-workspace, hermes-agent, homelab-host-operations, homelab-ssh-routing, network-route-change, nexus-compose-storage, obsidian, pdf, playwright, powerpoint, xlsx.

## Observed usage

| Client | Retained coverage | Recorded requests |
|---|---:|---:|
| Codex on tensor | 3 session files | 15 explicit read requests |
| Codex on nexus | 1 session files | 5 explicit read requests |
| Codex on qubit | 5 session files | 6 explicit read requests |
| Nexus Hermes | 106 sessions / 13672 messages | 526 skill_view requests |

Hermes native counters separately retain 28 loads across nine metadata entries. They are not added to session history because the sources overlap and have different retention. Historical names and removed skills remain in statistics. No recorded use means unknown usage outside retained records.

Codex counts identify explicit read requests in retained function-call records. They do not establish successful reads. Hermes counts identify skill_view calls; native view/use counters both measure loading. None of these metrics measures usefulness, token savings or cost attributable to a skill.

## Most requested Hermes skills in retained history

| Skill name recorded | Requests | Kept now |
|---|---:|---|
| homelab-host-operations | 81 | yes |
| autonomous-ai-agents/hermes-agent | 72 | yes |
| systematic-debugging | 52 | no |
| superpowers:test-driven-development | 26 | no |
| Homelab change journal | 23 | no |
| superpowers:verification-before-completion | 23 | no |
| superpowers:executing-plans | 21 | no |
| Homelab token efficiency | 20 | no |
| Homelab history retrieval | 19 | no |
| homelab-history | 15 | no |
| homelab-token-efficiency | 15 | no |
| writing-for-agents | 14 | no |
| grounded-citations | 13 | no |
| project-learning-loop | 11 | no |
| superpowers:brainstorming | 9 | no |

## Changes and controls

Removed 85 canonical skills; rollback source is the private [backup branch](https://github.com/iragonforce/backup/tree/skills-cleanup-2026-11-05), commit 0b5f451091171baf4b6b30742a1ce8b92a19f4b8. Only removed skill content was committed; no credentials or session databases.

Hermes skill writes require review, skill-creation nudges are disabled, and autonomous curation is disabled. One-time work goes into project notes. This controls native skill management; it is not a sandbox against arbitrary terminal writes.

Nexus API credential bindings are fetched from Bitwarden into /run/agent-credentials by agent-secrets.service. The bootstrap credential is TPM encrypted; plaintext bootstrap copies and 94 obsolete credential-bearing backup/cache files were removed. Docker configuration contains no migrated credential environment values. Hermes rejects anonymous API requests (401) and accepts its Bitwarden-sourced credential (200). All 25 MCP connections passed initialize/tools-list checks after migration.

Active Hermes/Codex provider-managed OAuth files remain local, with verified snapshots in Bitwarden. Linux has no available native keyring service; Qubit Keychain import was blocked by macOS (-25308) pending local Keychain interaction. SSH keys and storage snapshots were preserved. Old ZFS snapshots may retain historical plaintext; this cleanup does not erase them or prove that no secrets exist anywhere on a machine.

Rollback: restore selected skill directories from the backup branch after owner review. Credential references live in /etc/agent-secrets/refs.json (root-only); restore values from Bitwarden when needed. TPM ciphertexts are in /etc/credstore.encrypted. Reverting secret delivery requires preserving those references and active OAuth files; never blindly delete credentials. No new timestamp backup folders, telemetry hooks, cron jobs or formal tests were added.

Syncthing version archives and timestamp unification backups were removed on all three hosts. Both maintained setup scripts now avoid automatic backup copies; skill rollback remains in the private backup branch. Hermes history includes 15 create and 47 patch operations in retained skill_manage calls.

Boot handling: Hermes mounts the volatile credential file directly, so it cannot start with a missing credential mount. The existing boot service retries Bitwarden retrieval and restarts Hermes if Docker has already started. A new-container start was checked; a physical reboot with these latest secret-delivery changes has not been performed. Tensor and Qubit Bitwarden bootstrap files also remain in their existing private stores pending secure replacement. Codex read-request matching is heuristic and may miss implicit loads.


### 2026-11-06 — Qubit Keychain migration completed locally

Owner ran the prepared local migration. Observed: Codex auth.json and Bitwarden access-token plaintext files are absent; both Codex Auth and Homelab Bitwarden Keychain items exist. Codex now requires native keyring storage; the Bitwarden helper reads Keychain. The local helper required Codex login-status success and Bitwarden value equality before removing files. SSH follow-up cannot decrypt either credential: macOS reports interaction not allowed (-25308), not a logged-out status. Local migration is complete; SSH credential access remains unresolved. No plaintext fallback was restored.
