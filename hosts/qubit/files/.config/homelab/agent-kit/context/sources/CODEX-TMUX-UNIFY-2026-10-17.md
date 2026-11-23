# Codex and tmux layout across Qubit, Tensor, Nexus — 2026-10-17

## Changes

- Canonical `tmux/tmux.conf`: status-left shows `#{host_short}` in brackets; both window formats have spaces around `#I:#W`. Installed and sourced live on all three hosts. No tmux server or application was restarted.
- Qubit and Nexus `~/.codex/config.toml`: added Tensor's existing 13-item TUI `status_line` covering model, directories, context, limits, version, tokens and session ID. Tensor already had the same list.
- Tensor: installed `pdf@openai-primary-runtime`, `browser@openai-bundled`, `chrome@openai-bundled`, `computer-use@openai-bundled`, and `context-mode@context-mode`. Its existing documents, spreadsheets and presentations plugins remain enabled. Existing connected account plugins and disabled `browser-use` setting were preserved.
- Nexus: added the trusted context-mode Git marketplace and installed `context-mode@context-mode`. Account-connected plugins remain enabled.

## Checks and limits

- Live tmux option readback on Qubit, Tensor and Nexus shows `[#{host_short}] ` and ` #I:#W `. Sessions remained Qubit `main` (6 windows), Tensor `1` (5) and `main` (1), Nexus `nexus` (7).
- Parsed all three Codex TOML files: each TUI status list has 13 entries and ends with `session-id`. A newly started Codex session is needed to visually check the rendered line; running sessions were preserved.
- Tensor's enabled local set is 8 of Qubit's 13. Its installed Linux marketplaces do not offer `template-creator`, `visualize`, `codex-app-tools`, `unified-computer-use`, or `code-review`. Nexus's npm CLI offers no primary or bundled marketplace, so only context-mode from Qubit's local set could be installed there. The CLI rejected a Tensor Linux primary marketplace copy because `openai-primary-runtime` is a reserved source name; the temporary copy was removed. No macOS runtime cache was copied.
- This work did not exercise a real browser/plugin session on either Linux host. Earlier OSC 52 clipboard acceptance limits remain separately recorded.

## Backups and rollback

- Qubit: `/Users/iragonforce/.local/state/codex-tmux-unify-20261017-144630/` contains `qubit-codex-config.before` and `qubit-kit-tmux.conf.before`.
- Tensor and Nexus: `/home/iragonforce/.local/state/codex-tmux-unify-20261017-144630/` on each host contains `codex-config.before` and `tmux.conf.before`.
- Restore each saved Codex config and tmux config to its corresponding home path; restore Qubit's kit tmux source, then run `tmux source-file ~/.tmux.conf` on each host. No tmux restart is needed.
- To reverse only plugin changes, on Tensor run `codex plugin remove` for the five newly installed selectors listed above; on Nexus remove `context-mode@context-mode`. Then run `codex plugin marketplace remove context-mode` on both hosts. Restore saved Codex configs if needed. Existing plugin selectors are unchanged.
