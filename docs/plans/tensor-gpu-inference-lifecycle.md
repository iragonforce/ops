# Tensor GPU inference lifecycle and persistent job queue

**Status:** Stage 1 complete; Stage 2D two-phase restoration validated in synthetic tests; production service integration pending
**Date:** 2026-11-24
**Host:** `tensor` (Arch Linux, NVIDIA RTX 5070, 64 GB-class RAM)
**Scope:** Hermes/llama.cpp, Ollama, MinerU, Nexus-initiated Qdrant embeddings, Hyprland desktop restoration
**Repository policy:** `iragonforce/ops` is the authoritative deployment source. Publish sanitized, reviewed configuration and implementation snapshots to `iragonforce/tensor`; never publish private runtime queue contents.

## Objective and operating contract

A shared, crash-recoverable GPU admission mechanism shall let multiple inference and document-processing requests wait safely without evicting each other. **Background** work must not purge VRAM or start GPU-heavy tasks while the user is active. When the desktop is eligible for background processing, it should stop only known, restorable GPU services, run queued work, and restore the previous desktop state after the final GPU reservation ends. An **explicit foreground** inference request may request priority, but must not silently kill arbitrary user applications. For unscheduled direct Ollama HTTP clients, guarantee this contract only after they are routed through the admission mechanism.

Keep a usable status/queue interface (`status`, `list`, `submit`, `cancel`, `retry`, `pause`, `resume`) and durable evidence for completed/failed work. Avoid adding another LLM, memory database, orchestrator, periodic polling daemon, or duplicated Qdrant inbox.

## Verified baseline (2026-11-24, historical observation)

- `llama-cpp`, `ggml`, and `ggml-cuda` 1.0.0-1 installed on Tensor; `llama-server` exposes `--no-kv-offload` and `--sleep-idle-seconds`.
- Hermes v0.22.5 currently has a custom provider, default `qwen3.8-27b-iq3`, base URL `http://127.0.0.1:8080/v1`, and 64K context. Its gateway has a systemd drop-in depending on `hermes-llama.service`.
- `Qwen3.8-27B-UD-IQ3_XXS.gguf` is present at `~/.local/share/llama.cpp/models/` (10,934,860,704 bytes). After stopping Wallpaper Engine's supervisor, `hermes-llama.service` reached active/HTTP `/health` OK, with 10,590 MiB of 12,227 MiB GPU memory used. Actual KV/recurrent-state device placement and Hermes tool use remain **unverified**.
- `hermes-llama.service` includes an `ExecStartPre` purge and a drop-in that first stops `wallpaper-engine-sync.service`; `ExecStopPost` restarts Wallpaper Engine. It does not automatically stop the model after the final inference request. Idle GPU VRAM remains occupied.
- `wallpaper-engine-sync.service` supervises children on both monitors; killing `linux-wallpaperengine` directly causes them to respawn. Its systemd `KillMode=control-group` allows a scoped stop.
- System Ollama is active at port 11434; the Tensor user Ollama service is inactive. An embedding model may be loaded on demand. Nexus Qdrant indexer sends `/api/embed` to Tensor with model `qwen3-embedding:8b-fp16`, currently `keep_alive: 10m`.
- `mineru-webui.service` and its API/router processes remain active as long-lived frontend infrastructure; a running WebUI is **not evidence** that a PDF GPU job is active.
- Hypridle has an existing 300-second idle rule; `tensor-idle-media` and desktop/session tooling exist. Hypridle and media-awareness are documented, but production admission must still verify idle/resume transitions and remote-session vetoes before enabling live GPU work.
- `~/.local/bin/vram-purge --worker` currently signals a broad set of user processes. It must **not** run unattended as a general-purpose queue admission step.

All baseline observations require revalidation before modifying live services. In particular, check current service/port/process state and worktree status, not only this document.

## Stage 0 follow-up evidence — 2026-11-24

- `hypridle` is running (PID 1269). Its live 300-second listener invokes `tensor-idle-action`; `tensor-idle-media` gates it and is retried every 15 seconds. No queue idle/resume hooks are installed.
- `loginctl show-user iragonforce` reports `IdleHint=no` with five sessions (including `seat0` and remote/terminal sessions). This is **not a confirmed, usable background-idle signal**. Validate the graphical session and event transitions before using it for admission.
- `hermes-llama.service`, `hermes-gateway.service`, `mineru-webui.service` and `hypridle.service` were active at inspection. A running MinerU WebUI alone does not establish a GPU conversion in progress.
- `~/ops` was on `consolidate` with no tracked/untracked differences reported by `git status --short` in the supplied output. Repository branch/working-tree state is a dated observation and must be refreshed before writing.
- The graphical login session `2` on `seat0` is Wayland, `Class=user`, `Active=yes`, `Remote=no`, `State=active`, `IdleHint=no`. This confirms a locally active session, **not** current keyboard/mouse activity or a reliable five-minute idle indication.
- On the same inspection, `sunshine.service` and `moonlight-dock.service` were both inactive. Future active streaming must remain an explicit admission veto; these are point-in-time observations.
- Listener inspection found MinerU on `0.0.0.0:7860`, llama.cpp on `127.0.0.1:8080`, and Ollama on port `11434` (address/listener inferred from `ss`, no client inventory established).
- The limited `find ... -maxdepth 3 -iname '*queue*' -o -iname '*worker*'` returned no MinerU files; this **does not** prove MinerU lacks an application/native queue. Its API submission/worker and output completion boundaries still require source inspection.
- Existing five-minute `on-timeout` directly calls `tensor-idle-action`, which can enter visual standby. The background scheduler must coordinate with the existing action to avoid an idle-transition race; do not add a second independent five-minute worker trigger.
- Follow-up: the existing MinerU Gradio WebUI uses `demo.queue(default_concurrency_limit=1)` and conversion tasks use `asyncio.create_task` / `asyncio.to_thread`; durable submission and failure checkpointing are not yet established. `hibernate enter` is visual standby, retaining network and processes. The remaining native idle signal and remote/Ollama/request boundaries are explicitly deferred to Stage 2–5 adapter validation; **automatic purge remains prohibited**.

## Non-negotiable constraints

1. Keep Hyprland, tmux, authentication, the Ollama API, the Hermes gateway, and the MinerU WebUI available; do not kill unknown graphical applications or unsaved work.
2. Protect active inference: never purge or unload a model still serving requests. Serialize incompatible GPU workloads; no overlapping heavy loads on 12 GB VRAM.
3. Treat background requests as **durable pending jobs**. Never acknowledge completion before the actual output, embedding upsert and source checkpoint are committed. Job failure/crash must retain enough information for safe retry.
4. Idle/remote-session signal unavailable or ambiguous → do not admit automatic GPU-intensive work. Pause intake on user activity; finish or checkpoint the active job at a safe boundary.
5. Stop Wallpaper Engine only if it is active when the first GPU lease is acquired; restore only that preexisting state after the final lease and confirmed VRAM release. Coordinate session startup's independent wallpaper restart path.
6. Queue files, document paths, intermediate content, private model data, secrets, logs and operational checkpoints stay in protected local state, not public Git. Include `capture` for user-run diagnostics, with stderr and no credential output.
7. Use small reversible stages, source-managed changes, scoped backups, explicit rollbacks and independent validation. Do not migrate working Nexus Qdrant data or change its collection.

## Stage 0 — Confirm current state and safe integration boundaries

**Actions:** Read `AGENTS.md`, `docs/START-HERE.md`, relevant `docs/current`, and current Tensor source. Check Git status and history in both repos. Inspect live Hypridle/logind activity, Sunshine/Moonlight detection, local/remote Ollama request paths, MinerU job submission/worker model, and Hermes gateway/request lifecycle. Verify whether Ollama or MinerU have existing queues and whether their controls are sufficient. Record ownership of each changed file.

**Gate:** Produce an evidence-backed inventory of active triggers, idle signals, long-running frontends vs real jobs, GPU workload completion signals, and current rollback files. No production changes in this stage.

**Rollback:** None (read-only).

## Stage 1 — Durable queue and policy, dry-run only

**Actions:** Reuse existing native job/inbox facilities wherever possible. For new Tensor-only jobs, implement a minimal protected on-disk queue with atomic submission, stable job ID, kind/source/priority/status, retry count, safe output/checkpoint references and interruption recovery. A single `flock`/systemd-managed worker prevents concurrent GPU admissions. Use existing Hypridle idle/resume events and systemd activation rather than a polling daemon; policy supports dry-run, status, pause/resume and bounded retry/backoff. Never store arbitrary transcripts or embed files in public source.

**Gate:** Synthetic tests show FIFO within priority, deduplication, multiple files queued without blocking, active-user deferral, interrupted job recovery, cancelled/failed job preservation and no GPU/Wallpaper changes. Validate secure permissions and that repeated submissions cannot duplicate completed work.

**Rollback:** Disable queue activation; preserve pending queue records and return to direct application paths.

## Stage 2 — Safe GPU lease and desktop restoration

**Actions:** Acquire a resource reservation atomically before touching the desktop; record whether Wallpaper Engine was running. Stop `wallpaper-engine-sync.service` and wait for child exit. Check free VRAM and only unload explicitly known idle inference models. Do not invoke the broad `vram-purge --worker` as the unattended policy. On release, verify model memory has actually unloaded, then restore Wallpaper Engine if and only if it was previously active and no other lease exists. Handle service failures, SIGTERM, reboot/recovery and an external wallpaper restart during a lease.

**Gate:** Simulate acquire/release, two consumers, failure before model load, failure during job, respawning wallpaper, and user activity; no premature restoration, no stray GPU process termination. Restore wallpaper after the last lease.

**Rollback:** Restore prior service/drop-in configs from targeted backup; keep the existing manual wallpaper start/stop commands available.

## Stage 3 — Hermes inference lifecycle

**Actions:** Remove the Hermes gateway's always-loaded-model dependency only after request-level activation is proven. Keep gateway alive while letting llama.cpp sleep/unload when idle. Route foreground CLI and gateway inference through the same reservation path; wait for `/health`, propagate failures immediately and keep model alive only for active requests / a bounded idle grace period. Verify CUDA GPU weight residency and CPU KV plus recurrent-state placement from current llama.cpp logs. Preserve the current `qwen3.8-27b-iq3` GGUF and provider rollback.

**Gate:** Hermes cold and warm starts, one real read-only tool call, concurrent sessions, gateway request, server crash and restart all pass; idle releases VRAM and restores Wallpaper Engine. A second session must not unload the first session's model.

**Rollback:** Restore previous `~/.hermes/config.yaml`, launcher and Hermes service/drop-ins; keep GGUF; previous Ollama endpoint remains available.

## Stage 4 — Ollama and Nexus Qdrant embeddings

**Actions:** Integrate the existing Nexus embedding writer at the request/batch boundary. Preserve its existing per-origin checkpoints and inbox retries; queue requests when Tensor is busy, and return/transmit completion only after the embedding and Qdrant write are verified. Adjust the current 10-minute `keep_alive` only after requests use the new admission path. Keep Ollama daemon up; do not force-stop active external clients. Enumerate and gate direct HTTP callers before promising global exclusivity.

**Gate:** Two independent embedding batches queue; Hermes retains its lease; queued batch resumes after release; failed inference produces no checkpoint advance; idempotent retry updates only intended points. Verify with Qdrant exact-ID readback and service logs, not merely an HTTP success response.

**Rollback:** Restore the prior writer invocation and retention setting; keep unfinished files/checkpoints intact. Do not prune Qdrant records.

## Stage 5 — MinerU document processing

**Actions:** Keep `mineru-webui.service` running. Identify its actual task creation, worker execution, outputs and cancellation boundaries. Integrate the PDF worker or submission endpoint (not the persistent WebUI) with the same durable queue; preserve input files and partial outputs. Prefer upstream/native job handling if available. Do not kill an active document conversion when the user resumes desktop activity; finish/checkpoint safely and defer the next item.

**Gate:** Multi-PDF batch is accepted without blocking; only one heavy job runs; active desktop delays the next job; failed conversions remain retriable; completed Markdown/PDF outputs are not duplicated or overwritten.

**Rollback:** Restore the existing WebUI/worker launch paths and leave outstanding documents available for manual/native retry.

## Stage 6 — End-to-end acceptance and public recording

**Actions:** Exercise boot recovery, idle-to-active transition, interactive Hermes preemption policy, model load failure, Ollama embedding with competing Hermes work, MinerU batch processing, and wallpaper restoration. Capture relevant timings, queue states, logs and checks without credentials or private content. Reconcile deployment source in `iragonforce/ops` first, then copy **reviewed non-secret implementation and configuration** into `iragonforce/tensor` with explicit `.gitignore` allowlisting, Gitleaks and focused commits. Do not publish live queue/runtime state.

**Gate:** All acceptance checks pass, source/live hashes recorded, recovery exercised and both repository revisions recorded. If any component cannot participate in coordination, document its exception instead of claiming full system-wide coverage.

**Rollback:** Scoped Git/source and unit restoration; preserve all submitted work and Qdrant data; verify baseline services and wallpaper operation.

## Progress ledger (update after each gate)

| Stage | Status | Evidence | Next action |
| --- | --- | --- | --- |
| 0 — Inspect integrations | **Complete for Stage 1** | Wayland seat0; Hypridle 300s; Sunshine/Moonlight inactive; MinerU Gradio queue concurrency 1; llama.cpp 8080, Ollama 11434; native GPU admission still unverified | Proceed with synthetic-only Stage 1 |
| 1 — Durable queue | **Committed and pushed** | 13/13 tests; 30 synthetic jobs; deduplication and private permissions verified | Commit 6be0ded |
| 2 — GPU lease/desktop restoration | **Restoration transport validated, source-only** | 165/165 tests; systemd unit verified; no production changes | Failure-injection and guarded live integration pending |
| 3 — Hermes lifecycle | **Native sleep/wake verified** | 300-second sleep; successful cold inference; 10,226 MiB released | Gateway request test and wallpaper coordination pending |
| 4 — Ollama/Qdrant | Not started | Existing `/api/embed` and checkpoints identified | After Stage 3 gate |
| 5 — MinerU | Not started | WebUI/router/backend processes identified | After Stage 4 gate |
| 6 — Acceptance/publication | Not started | — | After Stage 5 gate |

**Scope control:** Complete one gate at a time. Record changed files, actual verification output references, blockers, rollback and commit SHA here before starting the next stage. Do not interpret this plan as permission for destructive process termination, data pruning, credential changes or automatic deployment from the public Tensor snapshot.

## Stage 1 implementation record — 2026-11-24

Locally authored and tested (not deployed):

- `shared/scripts/tensor-gpu-queue.py`: Python standard-library SQLite queue; 0700 private directory, 0600 database, `BEGIN IMMEDIATE` atomic claims, WAL, unique synthetic source keys, priority/FIFO, leases, retry/backoff and operator CLI. No real tasks or auto-idle actions are executable in this stage.
- `shared/tests/test_tensor_gpu_queue.py`: 13 passing isolated tests, including 30-item batch/restart, duplicate-after-completion, two concurrent claimers, activity deferral, pause, failed/cancelled state, expired lease and private file modes.
- `man/tensor/tensor-gpu-queue.1`: usage and safety boundary.

The simulated `--activity idle` flag is a **test input only**, not a verified Hyprland idle signal. In particular, these tests do not authorize actual VRAM purging, GPU process termination, or production job dispatch. Completion of Stage 1 requires repeating acceptance on Tensor. Existing `hermes-llama.service` remains a separate running service outside queue authority until later stages.

## Stage 1 Tensor acceptance — 2026-11-24

- Host: Tensor (Arch Linux).
- Tests: 13/13 passed using Python unittest.
- Synthetic batch: 30 submitted and completed.
- Active simulation: 0 jobs executed; all 30 remained pending.
- Idle simulation: all 30 completed.
- Repeated submission: 0 new jobs, 30 reused.
- Private state: directory 0700; SQLite database 0600.
- Source installed in the authoritative ops checkout.
- No production worker, idle hook, GPU purge, or service modification.
- Next gate: safe GPU lease and desktop restoration.

## Stage 2 synthetic acceptance — 2026-11-24

- Tensor: 17/17 GPU lease tests passed.
- Stage 1 regression: 13/13 tests passed.
- Verified simulated shared leases, conflict rejection, crash recovery and restoration guards.
- Source: tensor-gpu-lease.py, corresponding tests and man page.
- No production worker or GPU adapter enabled.
- No Hermes, Ollama, MinerU, Wallpaper Engine or Hypridle modifications.
- Remaining Stage 2 gate: live systemd adapter, GPU memory-release verification and rollback.

## Stage 2 read-only probe acceptance — 2026-11-24

- Host: Tensor; probe mode: read-only.
- Tests: 11/11 probe, 17/17 lease, 13/13 queue passed.
- Observed VRAM: 10,590 MiB used, 1,242 MiB free.
- Hermes llama.cpp active with CUDA allocation.
- Ollama reported zero loaded models.
- Wallpaper Engine inactive.
- GPU admission denied as expected.
- No GPU workloads or systemd services changed.
- Remaining gate: reversible real-service adapter and restoration verification.

## Stage 2C adapter acceptance — 2026-11-24

- Tensor: 58/58 tests passed.
- Read-only systemd/NVIDIA adapter verified.
- Live Qwen CUDA process detected.
- GPU admission denied, as expected.
- No systemd or GPU workload changes performed.
- Production control remains disabled.
- Blocker: Hermes independently restores wallpaper.
- Blocker: Hyprland session-start independently restarts wallpaper.
- Blocker: dead-owner lease recovery not validated.
- Limitation: direct Ollama HTTP clients are not coordinated.
- Next: implement restart guards and recovery before controlled live acquire/release.

## Stage 2D preliminary acceptance — 2026-11-24

- Tensor: 72/72 tests passed across five suites.
- Lifecycle guard: 14/14 tests passed.
- Guard remained read-only; live control disabled.
- Missing lease state correctly denied wallpaper admission.
- No production worker, service hook or GPU modification.
- Three source files installed but not activated.
- Remaining: atomic owner registration, dead-owner recovery, Hermes/Hyprland restart guards, controlled live acceptance and rollback.

## Stage 2D owner recovery acceptance — 2026-11-24

- Host: Tensor; isolated Git worktree.
- Base revision: a4303f6.
- All six GPU test suites passed: 88/88.
- Added 16 owner-recovery tests.
- Lease ownership now records process identity.
- Confirmed-dead owners are recoverable without releasing surviving consumers.
- Unknown owner identities fail closed.
- Model-memory verification still gates desktop restoration.
- No live GPU service modifications.
- Remaining: wallpaper restart arbitration, controlled live verification and rollback.

## Stage 2D wallpaper arbitration acceptance — 2026-11-25

- Host: Tensor, isolated feature worktree.
- 110/110 GPU tests passed, including 22 arbitration tests.
- Zero SQLite ResourceWarnings after test cleanup.
- Same-lock synthetic startup arbitration validated.
- Unknown lease state and GPU residency fail closed.
- No live service hooks or GPU changes performed.
- Remaining: two-phase restoration handoff, Hermes/Hyprland integration, controlled live verification.
- Existing direct Ollama clients remain outside admission.

## Stage 2D two-phase restoration acceptance — 2026-11-25

- Host: Tensor, isolated feature worktree.
- Base revision: 60f8f9b.
- Initial candidate: 124 tests, two regressions.
- Corrected implementation: 127/127 tests passed.
- Zero SQLite ResourceWarnings.
- Durable restoration grants and replay protection validated in synthetic tests.
- Failed restoration retains recoverable state.
- No production service hooks activated.
- No Hermes, Ollama, MinerU or Wallpaper Engine configuration changes.
- Remaining: guarded systemd startup integration, targeted rollback and controlled live acceptance.

## Stage 2E systemd source acceptance — 2026-11-25

- Host: Tensor; isolated systemd integration worktree.
- Base revision: 0383c4c.
- GPU regression tests: 143/143 passed.
- Candidate systemd unit passed static verification.
- Guarded Type=notify entrypoint added in source only.
- Existing wallpaper supervisor and renderer retained.
- Production Hermes and wallpaper services remained active.
- No live lease database initialization or service changes.
- Remaining: restoration-grant transport, Hermes/Hyprland
  startup integration, crash recovery and live acceptance.
- This checkpoint does not authorize production deployment.

## Stage 2F restoration transport acceptance — 2026-11-25

- Host: Tensor.
- Base revision: 46c6869.
- GPU regression suite: 165/165 passed.
- Private restoration mailbox and adapter integration validated in synthetic tests.
- Candidate systemd unit passed static verification.
- Exactly seven implementation files changed.
- Hermes and Wallpaper Engine remained active.
- No production database or service modifications.
- Remaining: READY/SQLite failure-injection, Hermes/Hyprland integration and controlled deployment.
- Source-only acceptance does not authorize live activation.

## Stage 3 native sleep pilot — 2026-11-25

- Host: Tensor.
- Native llama.cpp idle timeout: 300 seconds.
- Model: Qwen3.8-27B-UD-IQ3_XXS.gguf.
- Model entered sleep without stopping the service.
- Cold inference with managed wallpaper stopped: HTTP 200.
- Completion: 33 generated tokens.
- GPU usage after inference: 11,193 MiB.
- GPU usage after second sleep: 967 MiB.
- Measured VRAM reduction: 10,226 MiB.
- Hermes gateway remained active.
- Wallpaper start was requested after the test.
- Subsequent verification found the wallpaper service inactive.
- Persistent wallpaper restoration is NOT verified.
- Cold wake with wallpaper running is NOT verified.
- Existing GPU queue and lease guard remain undeployed.
- Rollback: remove 30-native-sleep.conf, reload user systemd,
  and restart hermes-llama.service in a maintenance window.
