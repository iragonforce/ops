# Set Hermes Antigravity fallback order

Date: 2026-11-12
Host: nexus
Project: `hermes-kanban/hermes` / Docker Compose project `hermes`

## Objective

Use Claude Sonnet 4.6 first, followed by Gemini 3.8 Flash, as the
Antigravity fallback chain while preserving Hermes's existing primary
provider and default model.

## Changes

- Replaced the single `antigravity-agy` / `gemini-3.8-flash-medium`
  fallback with two entries, in order:
  1. `antigravity-agy` / `claude-sonnet-4-6`
  2. `antigravity-agy` / `gemini-3.8-flash-medium`
- Kept `openai-codex` / `gpt-6-sol` as the primary.
- Restarted only the Hermes container to load the updated chain.
- No plugin, Compose, image, or credential changes.

## Verification

- `hermes fallback list` read back both entries in the requested order
  and the unchanged primary model.
- The live `agy models` list includes `claude-sonnet-4-6` and
  `gemini-3.8-flash-medium`.
- A one-shot Hermes request directly through
  `antigravity-agy` / `claude-sonnet-4-6` returned `sonnet-ok`. This
  validates that model route; the request did not exercise automatic
  fallback from the primary.
- After restart, the Hermes container was `running/healthy` and
  `http://127.0.0.1:8642/health` returned status `ok`, version
  `0.21.6`.
- No formal test suite or dashboard/messaging conversation was run.

## Rollback

To restore the previous Gemini-only chain, clear the entries with
`hermes fallback clear`, add `antigravity-agy` /
`gemini-3.8-flash-medium`, then restart Hermes. A root-only pre-change
config copy is retained at
`/var/backups/homelab/hermes-config-before-sonnet-then-flash.yaml`
(mode 0600; SHA-256
`cb11b7ab0c2b8afbdb57ff30317b769f5310dc37e3aacb7b37921ba6116fbc75`).
Restore the whole file only if no later config edits need to be retained.

## Source and deployment

The canonical non-secret record is this file and the current Hermes
summary in `docs/current/README.md`. Runtime configuration remains at
`/srv/containers/data/hermes/data/config.yaml`; the Compose source
`hosts/nexus/files/srv/containers/compose/hermes/compose.yaml` was not
changed.
