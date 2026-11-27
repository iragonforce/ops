# Current infrastructure facts

Verified 2026-11-06 unless marked otherwise. Task-specific physical acceptance remains separate.

| Host | Role | Agent state | Access |
|---|---|---|---|
| qubit | macOS control machine | Codex CLI 0.167.0; Nexus Hermes SSH launcher; no local Hermes home | Existing strict-key SSH route works |
| tensor | Arch desktop | Native Hermes gateway with local llama.cpp `qwen3.8-27b-iq3`; fail-closed GPU lease policy admits real prompts and a transient queued Ollama embedding worker ran a local sample; Nexus Qdrant and MinerU production dispatch not yet enabled | Strict-key SSH route verified November 27 |
| nexus | Debian 13 NAS/Docker/KVM | Codex CLI 0.166.0; Hermes v0.21.6 Coordinator, native Kanban and openai-codex provider; redundant Qwen Hermes and Paperclip retired | Local execution host for this implementation |

## Main Hermes

As verified on 2026-11-08, Nexus Hermes uses provider
`openai-codex` with default model `gpt-6-sol`; a one-shot
inference request passed. Its native Kanban dashboard is
available at `https://hermes.blinkwired.com` behind Authentik.

On 2026-11-12, the `fallback_providers` chain was set to
`antigravity-agy` / `claude-sonnet-4-6`, followed by
`antigravity-agy` / `gemini-3.8-flash-medium`. The primary
provider and default model remain unchanged. The container's
existing `agy` 1.4.11 installation and signed-in credential
passed status checks. A one-shot Hermes request through Claude
Sonnet 4.6 returned successfully; after restart, the gateway's
health endpoint passed. Dashboard and messaging runs remain
unverified. See
[`2026-11-12-hermes-antigravity-fallback.md`](../changes/2026-11-12-hermes-antigravity-fallback.md)
and
[`2026-11-12-hermes-fallback-order.md`](../changes/2026-11-12-hermes-fallback-order.md).

Tensor runs an independent native Hermes gateway using provider `custom` and
llama.cpp at `http://127.0.0.1:8080/v1`, default `qwen3.8-27b-iq3`, context
64000. The November 26 unguarded `/slots` wake caused a CUDA OOM while Ollama
occupied VRAM. The November 27 required-middleware cutover initially denied
every prompt because no actual policy was installed; a later cutover deployed
the GPU lease plugin, its fixed read-only tools, and the Git-owned wrapper.
Real default CLI prompts then exited successfully, with llama stopped and the
lease released. A transient Tensor worker completed one queued local embedding
sample, verified its input digest/vector and released its GPU lease; this is
**not** Nexus Qdrant writer acceptance. Local Ollama tags are discoverable, but
Ollama chat and model-side tool invocation are not accepted. Wallpaper
active→stopped→restored has not been verified in an interactive desktop session.
Nexus writer transport and MinerU conversion are not deployed. See the
[live admission record](../changes/2026-11-27-tensor-gpu-live-admission.md)
and the earlier [fail-closed cutover](../changes/2026-11-27-tensor-hermes-gateway-failclosed-cutover.md).
After the owner's November 26 authorization, direct non-loopback Tensor
Ollama (:11434) and MinerU WebUI (:7860) ingress and Tailscale Serve 8445
were briefly restricted and then **restored** by verified targeted rollback.
Direct clients are available again while the guarded replacement is built;
Tensor-local loopback callers would not be gated by the candidate network rule.
See the [ingress record](../changes/2026-11-26-tensor-gpu-ingress-containment.md).
See the [incident record](../changes/2026-11-26-tensor-llama-cold-wake-oom.md)
before trying to restart it. The earlier Ollama `gpt-oss:20b` default and
`qwen3.5:9b` test are historical, not current configuration. See
[`tensor-gpu-inference-lifecycle.md`](../plans/tensor-gpu-inference-lifecycle.md).

The duplicate Nexus `qwen-hermes`, Paperclip, API relays,
Knowledge Bridge and Spectrum containers have been retired.
Historical Paperclip, Qwen and OpenClaw data is preserved.
The Knowledge Bridge anonymous Docker volume remains present,
with a verified archive under
`/srv/containers/data/hermes/legacy-backups/knowledge-bridge/`.
Do not prune that volume or delete historical directories
without a separate retention decision.

Native Hermes Kanban is the selected task system, but automated
specialist routing, production handoffs and crash recovery are
not yet accepted. The archived `infra-pilot` board remains
historical evidence, not active production intake.


Maintained Compose: `/srv/containers/compose/hermes/compose.yaml`. Persistent host directory `/srv/containers/data/hermes/data` is container `/opt/data`. On 2026-11-07, dormant `devops` and `research` profiles were added for the completed, now-archived pilot; see [specialist status](specialists.md). The November 7 specialist pilot remains archived; autonomous specialist execution requires separate acceptance testing and authorization. The supervised main process runs as UID 10000; Docker's configured root user does not describe that process's UID.

At audit, `state.db` held 106 sessions/13,672 messages and native FTS queries worked. Native session search appeared 22 times in four retained sessions. Saved main model was `gpt-6-sol`; no model change is authorized by this project.

Main memory was repaired on 2026-11-06: 1,152 characters in three entries against the unchanged 2,200-character limit. The prior 3,878-character memory blocked additions and contained obsolete topology. USER.md was preserved. See the knowledge change record for exact native import/search results and rollback.

## History and evidence

Existing archive: `/srv/containers/data/paperclip/migrations/20261017/public/history.sqlite`, 101,524 distinct chunks and 176,389 occurrences. The source manifest contains Codex rollout files from Qubit (8), Tensor (116), Nexus (2). Private originals remain in sibling `private/archives`. Historical redaction was best-effort; none of those contents belongs in Git.

Three selected archived Codex conversations (one per host) now have native Hermes sessions and verified keyword retrieval. The private deduplication/provenance ledger is `/opt/data/import-ledger/codex.json`. Native `hermes sessions import --from codex FILE` imports conversation text, omits tool outputs, and creates a new ID on every import. Native `import-agent codex` imports agent setup, not session history. Preserve provenance and deduplicate explicitly. Do not resume imported historical tasks as new infrastructure commands.

## Stable boundaries

Nexus Compose `/srv/containers/compose`; data `/srv/containers/data`; builds `/srv/containers/builds`; private credentials `/etc/nexus/secrets`. Container `/mnt/fast` maps active host data, not the original pool root. Preserve storage datasets, radio identities, VLANs and routes. Sonoff is Zigbee2MQTT, Nordic Thread/OTBR, ZBT-1 spare. Tensor visual standby keeps processes/network awake.

Bitwarden delivers main Nexus API bindings through `agent-secrets.service` into `/run/agent-credentials`. Bootstrap is TPM encrypted. Active provider OAuth stays in existing private stores. Qubit Keychain migration was previously verified locally; SSH Keychain access remains limited.

## Existing issues outside this task

Tensor reported failed NFS mount/recovery, boot-notification, system Ollama, wake-source and Ethernet-stability units after connectivity returned. No repair attempted. An independent user Ollama instance or other endpoint must be inspected before claiming model service failure from the system-unit result.

Physical desktop, clipboard, display and radio acceptance cannot be inferred from configuration or container health. Preserve dated pending records.

## Syncthing and Hermes fast-pool storage

Verified on Nexus, 2026-11-11.

- Syncthing Compose project: `nexus-syncthing`.
- Six retained shares: project, screenshots, downloads,
  documents, 3d-models and secondBrain.
- The first five use host directories `/mnt/fast/<folder>`.
- secondBrain remains `/home/iragonforce/secondBrain`.
- The three `homelab-unified-*` Syncthing shares were removed
  on Nexus; the owner also reported their removal on Tensor
  and Qubit. Local files and directories were retained.
- All six Nexus folders reached idle with zero pending
  files, deletions and reported errors. Both peers were
  connected at verification.
- Hermes retains `/srv/containers/data` mounted at
  `/mnt/fast` inside its container, with five specific
  `/mnt/fast/<folder>` bind mounts overriding the old paths.
- Hermes UID 10000 filesystem access and container health
  passed. Kanban board directories and profile instructions
  remained accessible.
- Original directories remain for recovery and may diverge
  from the new synchronized locations.
- Kanban application-level functionality has not been
  independently acceptance-tested after recreation.

See `docs/changes/2026-11-11-syncthing-hermes-storage.md`.
