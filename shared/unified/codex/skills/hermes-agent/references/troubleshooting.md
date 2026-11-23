# Troubleshooting

### Voice not working
1. Check `stt.enabled: true` in config.yaml
2. Verify provider: `python -c "import pm; pm.sync_venv(['stt-whisper'], explicit=True)"` or set API key
3. In gateway: `/restart`. In CLI: exit and relaunch.

### Tool not available
1. `hermes tools` — check if toolset is enabled for your platform
2. Some tools need env vars (check `.env`)
3. `/reset` after enabling tools

### Model/provider issues
1. `hermes doctor` — check config and dependencies
2. `hermes auth` — re-authenticate OAuth providers (or `hermes auth add <provider>`)
3. Check `.env` has the right API key
4. **Copilot 403**: `gh auth login` tokens do NOT work for Copilot API. You must use the Copilot-specific OAuth device code flow via `hermes model` → GitHub Copilot.

### Changes not taking effect
- **Tools/skills:** `/reset` starts a new session with updated toolset
- **Config changes:** In gateway: `/restart`. In CLI: exit and relaunch.
- **Code changes:** Restart the CLI or gateway process

### web_extract shows a stale page (result caching)
`web_search`/`web_extract` cache results for 20 minutes (PR #94618) — a
repeat fetch of the same URL within the TTL is served from cache, which
can look like "my website changes aren't showing up."

Automatic carveouts (always fetched live, never cached):
- localhost / 127.0.0.1 / `*.local` / `*.localhost` / single-label LAN
  hostnames / private + link-local IP ranges (dev servers, hot-reload
  builds, chat-GUI artifact previews)
- URLs matched by `security.website_blocklist`
- failed responses and keyless-rescue-served responses

Developing a site tested over the PUBLIC internet (Vercel/Netlify
preview, ngrok/cloudflared tunnel, staging domain)? Public DNS isn't
auto-carved-out — list the host in config.yaml:

```yaml
web:
  cache_exempt_hosts:      # always fetched live; effective immediately
    - mysite.vercel.app
    - "*.ngrok-free.app"
    - mysite.dev           # suffix match: also covers preview.mysite.dev
```

Blunt instruments: `web.cache_ttl_minutes: 1` (min) or
`web.cache_enabled: false` disables both caches entirely.

### Skills not showing
1. `hermes skills list` — verify installed
2. `hermes skills config` — check platform enablement
3. Load explicitly: `hermes -s name` (or the skill's own `/<name>` slash command)

### Gateway issues
Check logs first:
```bash
grep -i "failed to send\|error" ~/.hermes/logs/gateway.log | tail -20
```

Common gateway problems:
- **Gateway dies on SSH logout**: Enable linger: `sudo loginctl enable-linger $USER`
- **Gateway dies on WSL2 close**: WSL2 requires `systemd=true` in `/etc/wsl.conf` for systemd services to work. Without it, gateway falls back to `nohup` (dies when session closes).
- **Gateway crash loop**: Reset the failed state: `systemctl --user reset-failed hermes-gateway`

### Remote Hermes client, tmux, and terminal clipboard
1. Confirm where tools actually execute versus where the terminal is displayed. Resolve `ssh -G <host>` and try configured SSH aliases (including alternate interfaces), rather than treating a raw-IP timeout as proof of no access: aliases can select a different address, key, user, and trusted host identity. For a third host reachable only through a client, run the client's existing trusted SSH alias to that host instead of accepting an unverified new host key from a direct jump.
2. For drag-to-select and Command+C/Super+C inside tmux, inspect active `tmux show -gv mouse`, persistent tmux config, and the emulator's **effective** binding (`ghostty +show-config`), not just a preferred config file. On macOS Ghostty, check both `~/.config/ghostty/{config,config.ghostty}` and `~/Library/Application Support/com.mitchellh.ghostty/{config,config.ghostty}`: Application Support is loaded later and can silently override a correct XDG `super+c` binding with `text:\\x03` (Ctrl+C). Correct the effective override, run `ghostty +validate-config`, reload/restart the display-side Ghostty, then verify effective `super+c=copy_to_clipboard:mixed` again. The clipboard belongs to the Ghostty display host even when tmux/SSH/Hermes runs elsewhere; configure that client, not each remote host. GTK Ghostty supports `app-notifications = clipboard-copy,config-reload` for a copy toast; do not promise the same built-in toast on macOS. Ask the person at the display to confirm actual mouse/clipboard behavior.
3. Before restarting Ghostty or tmux, list all sessions, windows, panes, attached clients and pane child processes; check Neovim's modified-buffer state through its RPC socket when available. A full tmux server restart terminates unrelated pane programs (including remote agents) even if the Hermes conversation is saved. For configuration changes, prefer a live tmux `source-file` and Ghostty config reload; if the user explicitly requires a full restart, identify what will be terminated and coordinate it before killing the server. If the current Hermes CLI is in a pane being killed, arrange a safe return path before severing that session. Verify the new GUI has an attached tmux client and expected running panes, not merely a Ghostty PID or mapped window; starting a graphical app over SSH can leave a visible but empty window. Do not claim a reload is a restart or silently close an unrelated desktop window.
4. When removing old agent references across hosts, scan active shell/SSH/terminal/editor/launcher configs separately from historical notes, imports, recovery archives, and credentials. Remove confirmed dead navigation/config references with a rollback copy; preserve old private state and keys unless their deletion was specifically requested and safe ownership is established.

### Platform-specific issues
- **Discord bot silent**: Must enable **Message Content Intent** in Bot → Privileged Gateway Intents.
- **Slack bot only works in DMs**: Must subscribe to `message.channels` event. Without it, the bot ignores public channels.
- **Windows-specific issues** (`Alt+Enter` newline, WinError 10106, UTF-8 BOM config, line endings): see `references/windows-quirks.md`.

### Auxiliary models not working
If `auxiliary` tasks (vision, compression, session_search) fail silently, the `auto` provider can't find a backend. Either set `OPENROUTER_API_KEY` or `GOOGLE_API_KEY`, or explicitly configure each auxiliary task's provider:
```bash
hermes config set auxiliary.vision.provider <your_provider>
hermes config set auxiliary.vision.model <model_name>
```

### "Reset permissions" / auto-approving everything
See `references/security-privacy.md` — wipe the "Always allow" stores, don't touch yolo mode.

