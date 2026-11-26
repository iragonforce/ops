# Tensor llama.cpp cold-wake collision — 2026-11-26

## Objective and observed failure

During the authorized Stage 4–5 GPU-admission investigation, a diagnostic GET of Tensor's sleeping `llama-server` `/slots` endpoint at 10:38 EST **triggered a model wake**. This was not a safe read-only status probe. System Ollama had `qwen3-embedding:8b-fp16` resident on the same RTX 5070, and Wallpaper Engine's two renderers were active. The server attempted a 9685.21 MiB CUDA allocation, got `cudaMalloc failed: out of memory`, logged `failed to reload model after sleeping`, then aborted (`status=6/ABRT`, `Result=core-dump`). `hermes-llama.service` became failed at 10:38:29 EST. `hermes-gateway.service` remained active; HTTP inference on port 8080 was unavailable. Wallpaper Engine remained active. No process was killed or model purged by this investigation.

Evidence: Tensor `journalctl --user -u hermes-llama.service --since '2026-11-26 10:37:45' --until '2026-11-26 10:38:35'`, `systemctl --user show hermes-llama.service -p ActiveState -p Result -p ExecMainStatus`, `ollama ps`, and NVIDIA process/memory queries. The logs contain a core-dump trace; do not add the raw dump to Git. At 10:40, Ollama still held the embedding model with approximately six minutes of retention, GPU usage was 10589 MiB, the gateway and wallpaper services were active, and llama remained failed.

## Corrected assumption and safety boundary

`/slots` is **not** a safe sleeping-server status endpoint on this installed llama.cpp build. `/health` had previously returned HTTP 200 while asleep, but it also does not prove cold-wake admission safety. A model can load between a read-only GPU snapshot and an unguarded llama request. Do not restart llama while Ollama is loaded; do not use broad `vram-purge`, terminate an unknown GPU client, or repeat `/slots` as a diagnostic. The existing Stage 2 probe's `hermes_llama_not_inactive` veto is conservative, not a defect to bypass without a request-level reservation.

## Recovery and verification pending

Preserve the gateway, wallpaper, Ollama data, Qdrant records, queue files and MinerU outputs. After Ollama releases naturally, identify *all* current GPU owners and confirm available VRAM before a scoped llama service restart; its existing `ExecStartPre` stops the wallpaper supervisor, and its existing `ExecStopPost` starts it. Coordinate the visible wallpaper interruption and retain exact unit rollback. A restart that returns `/health` 200 alone is not full recovery: check an actual guarded inference, the subsequent native 300-second sleep, wallpaper restoration, and a second request with a competing embedding to prove deferral. If safe admission cannot be established, leave the service failed and report the exact blocker rather than recreating the collision.

No configuration or persistent data was modified by the failed probe. Source recovery is the pre-existing `e104b18` native-sleep drop-in; no version rollback or model deletion is authorized by this record. Production Stage 4–5 dispatch remains disabled until the shared request/lease boundary is implemented and tested.
