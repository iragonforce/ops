# Configuration, Toolsets & Voice

Edit with `hermes config edit` or `hermes config set section.key value`.
Full reference: https://hermes-agent.nousresearch.com/docs/user-guide/configuration

### Config Sections (most-used keys)

| Section | Key options |
|---------|-------------|
| `model` | `default`, `provider`, `base_url`, `api_key`, `context_length`, `aliases` |
| `agent` | `max_turns` (90), `tool_use_enforcement`, `service_tier`, `verify_on_stop` |
| `terminal` | `backend` (local/docker/ssh/modal/daytona/singularity), `cwd`, `timeout` (180) |
| `compression` | `enabled`, `threshold` (0.50), `target_ratio` (0.20) |
| `display` | `skin`, `interface` (cli/tui), `language`, `show_reasoning`, `show_cost`, `pet` |
| `approvals` | `mode` (smart/manual/off), `timeout`, `cron_mode` |
| `stt` | `enabled`, `provider` (local/groq/openai/mistral/elevenlabs/deepinfra) |
| `tts` | `provider` (edge/elevenlabs/openai/minimax/mistral/neutts/gemini/piper/kittentts/deepinfra/xai) |
| `memory` | `memory_enabled`, `user_profile_enabled`, `provider`, `write_approval` |
| `security` | `redact_secrets`, `website_blocklist` |
| `delegation` | `model`, `provider`, `max_concurrent_children`, `max_iterations` (50), `max_spawn_depth` |
| `checkpoints` | `enabled`, `max_snapshots` (50) |
| `curator` | `enabled`, `consolidate` (false, opt-in aux-model consolidation), `interval_hours`, `stale_after_days` |

`hermes config check` reports sections missing from an older config.

### Changing the compression model without changing chat routing

1. Resolve the active profile (`$HERMES_HOME`) and the Hermes execution environment. Read `hermes config get model.default`, `hermes config get model.provider`, `hermes config get auxiliary.compression.model`, and `hermes config get auxiliary.compression.provider`; distinguish the saved chat default from a running session's pinned model. Do not infer that changing compression also changes the chat model or its context length.
2. Check the current configuration docs or live source for the exact compression key and requested model identifier; preserve the identifier literally. If the owner supplied a model specifically for compression, change only `auxiliary.compression.model` unless they explicitly ask to reroute chat too. Keep the provider compatible with that model rather than silently inheriting an unrelated route.
3. Save a private, permission-restricted rollback copy of the active profile's `config.yaml` before a consequential change. Use `hermes config set auxiliary.compression.model <exact-model-id>` rather than editing YAML by hand.
4. Read back the compression model and provider, then compare parsed configuration before and after to ensure only intended keys changed. If runtime inspection is available, resolve the effective `compression` auxiliary task config too. A config readback verifies routing configuration, not that an actual compression request succeeded or that the provider accepted the model/context window; exercise a real compression request only when warranted and report that separately. Avoid restarting unrelated sessions or services merely to check the setting.

### Migrating deprecated environment settings

1. Resolve the active profile via `$HERMES_HOME` and identify where Hermes actually executes before inspecting files; a client terminal may only launch a remote/container profile. Check the current Hermes documentation and the specific warning's replacement key.
2. Read the replacement setting without printing secrets (`hermes config get terminal.cwd` for the legacy `MESSAGING_CWD` warning). Confirm the desired directory exists **on the execution host**. If unset, use `hermes config set terminal.cwd /path/on/execution/host`; do not substitute the client's current working directory by assumption.
3. Check only whether the exact obsolete key occurs in `$HERMES_HOME/.env`, withholding values. After the replacement is confirmed, make a permission-preserving private rollback copy and remove only that key's line; preserve every other byte, file mode, and unrelated setting. Do not print or diff the entire `.env` because it contains credentials.
4. Read back the replacement key and confirm the obsolete key is absent. If feasible, launch a fresh Hermes process and confirm the warning no longer appears; otherwise distinguish configuration verification from launch verification. Keep the rollback copy private and report its path.

### Toolsets

Enable/disable via `hermes tools` (interactive) or `hermes tools enable/disable NAME`.

For a toolset-enable request: identify `$HERMES_HOME` and the target surface first (`hermes tools list --platform cli` for a terminal session; `hermes tools enable --help` shows `--platform`). Enable only that profile/surface with `hermes tools enable NAME ...`, then read back `hermes tools list --platform <surface>`. Treat the enabled checkmark as configuration only: check feature prerequisites separately (browser backend/helper with `hermes tools post-setup agent_browser`, computer-use driver with `hermes computer-use status` and display/permissions with `hermes computer-use doctor`, voice provider and audio path per the current voice docs). Use `hermes pm install agent-browser` or `hermes computer-use install` when their respective helper is missing; repeat the readiness check after installing. In a container, computer-use controls the container's accessible display, not the remote terminal client's desktop. Report enablement and operational readiness separately; do not claim physical GUI or microphone behavior from a toolset listing.

Full enumeration: `TOOLSETS` dict in `toolsets.py` (`_HERMES_CORE_TOOLS` is the default bundle most platforms inherit).

| Toolset | What it provides |
|---------|-----------------|
| `web` / `search` | Web search + extraction / search-only subset |
| `browser` | Browser automation (Browserbase, Camofox, or local Chromium) |
| `terminal` | Shell commands and process management |
| `file` | File read/write/search/patch |
| `code_execution` | Sandboxed Python execution |
| `coding` | Code-editing helpers (LSP-backed) |
| `computer_use` | Desktop GUI control (cua-driver) |
| `vision` | Image analysis |
| `image_gen` | Image generation and image-to-image editing |
| `video` / `video_gen` | Video analysis / video generation |
| `x_search` | X (Twitter) search (X OAuth or API key) |
| `tts` | Text-to-speech |
| `skills` | Skill browsing and management |
| `memory` | Persistent cross-session memory |
| `session_search` | Search past conversations |
| `context_engine` | Pluggable context-engine hooks |
| `project` | Named multi-folder workspace tools |
| `delegation` | Subagent task delegation |
| `cronjob` | Scheduled task management |
| `clarify` | Ask user clarifying questions |
| `todo` | In-session task planning |
| `kanban` | Multi-agent work-queue tools (gated to workers) |
| `debugging` | Extra introspection tools (off by default) |
| `safe` | Minimal low-risk toolset for locked-down sessions |
| `spotify`, `discord`, `discord_admin`, `feishu_doc`, `feishu_drive`, `yuanbao` | Service integrations (gated on their credentials). `homeassistant` (`ha_*` tools) is not built in: it comes from the `homeassistant` catalog plugin (`hermes plugins install homeassistant`) |

Tool changes take effect on `/reset` (new session) — never mid-conversation, to preserve prompt caching.

## Voice

### STT (Voice → Text)

Voice messages from messaging platforms are auto-transcribed.

```yaml
stt:
  enabled: true
  provider: local   # local (faster-whisper, free) | groq | openai | mistral | elevenlabs | deepinfra
  local:
    model: base     # tiny, base, small, medium, large-v3, turbo
```

Auto-detect priority: local faster-whisper (`python -c "import pm; pm.sync_venv(['stt-whisper'], explicit=True)"`) → Groq (`GROQ_API_KEY`, free tier) → OpenAI (`VOICE_TOOLS_OPENAI_KEY`) → Mistral Voxtral (`MISTRAL_API_KEY`).

### TTS (Text → Voice)

| Provider | Env var | Free? |
|----------|---------|-------|
| Edge TTS (default) | None | Yes |
| ElevenLabs | `ELEVENLABS_API_KEY` | Free tier |
| OpenAI | `VOICE_TOOLS_OPENAI_KEY` | Paid |
| MiniMax | `MINIMAX_API_KEY` | Paid |
| Mistral | `MISTRAL_API_KEY` | Paid |
| Gemini | `GOOGLE_API_KEY` | Free tier |
| NeuTTS / Piper / KittenTTS (local) | None | Free |

Voice commands: `/voice on` (voice-to-voice), `/voice tts` (always voice), `/voice off`.
