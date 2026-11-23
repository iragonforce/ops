# Add Antigravity as a Hermes fallback provider

Date: 2026-11-12
Host: nexus
Project: `hermes-kanban/hermes` / Docker Compose project `hermes`

## Objective

Add the existing Google Antigravity provider as Hermes's first backup
model while keeping the current `openai-codex` provider and
`gpt-6-sol` default unchanged.

## Changes

- Used the existing provider plugin at
  `/opt/data/plugins/antigravity-agy` (pinned upstream revision
  `f85003d3ce0de3844e2d5c23174d630ff3586e5d`) and existing
  `/opt/data/.local/bin/agy` installation (version 1.4.11).
- Added `antigravity-agy` / `gemini-3.8-flash-medium` as the first
  entry in the runtime `/opt/data/config.yaml` `fallback_providers`
  list. No default model, provider credential, Compose file, or image
  was changed.
- Restarted only the Hermes container so the running gateway loads the
  updated configuration.
- Preserved the plugin checkout unchanged. It already had local edits
  to `__init__.py` and untracked catalog/backup files; those were not
  part of this change.

## Verification

- Before the change, `hermes fallback list` reported an empty chain;
  Hermes reported its primary as `openai-codex` / `gpt-6-sol`.
- `hermes auth status antigravity-agy` reported signed in, and the
  fallback picker recognized the provider and returned live models.
- After adding it, `hermes fallback list` read back the single
  `gemini-3.8-flash-medium` entry via `antigravity-agy`.
- A one-shot Hermes CLI request through the configured primary route
  returned `fallback-ok`; the primary credential was marked
  rate-limited during the preceding credential check. The CLI output
  did not include per-run provider metadata, so exact provider selection
  for that response is not independently asserted.
- After restart, the Hermes container was `running/healthy` and
  `http://127.0.0.1:8642/health` returned status `ok`, version
  `0.21.6`.
- No formal test suite was run. The dashboard and messaging gateway
  were not exercised with a user-visible conversation.

## Rollback

Remove the Antigravity entry with `hermes fallback remove` and restart
the Hermes container. A root-only pre-change config copy is retained at
`/var/backups/homelab/hermes-config-before-antigravity.yaml` (mode
0600; SHA-256
`6d9c2d701c83268fc8fe20482f630cf37f14edc3f764cdbfce4416ed054b28bd`).
Restore that whole config only if no later Hermes config edits need to
be retained.

## Source and deployment

The canonical non-secret record is this file and the current Hermes
summary in `docs/current/README.md`. The runtime configuration is stored
in Hermes's persistent data mount at `/srv/containers/data/hermes/data/config.yaml`;
the unchanged Compose source is
`hosts/nexus/files/srv/containers/compose/hermes/compose.yaml`.
