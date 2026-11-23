# Six-host Zsh source alignment — 2026-11-19

## Objective

Record the verified `iragonforce` and root `.zshrc`
configurations for Nexus, Tensor and Qubit in `iragonforce/ops`.

## Changes

- Imported three live user `.zshrc` files.
- Added three root `.zshrc` source snapshots.
- Registered root deployment targets with mode 0600 and
  the existing preserve-target policy.
- Added `docs/current/zsh-shells.md` as the configuration
  reference.

The existing user deployment baseline hashes are preserved.
The inventory's global capture timestamp is unchanged because
this is not a full inventory recapture.

## Previous runtime verification

- User configurations passed Zsh syntax checks on all hosts.
- Qubit, Tensor and Nexus root configurations passed their
  targeted interactive startup tests.
- Root prompts, native editors and 50-character history
  filters were checked.
- Nexus root command timing and integration availability
  were checked.
- Full SSH/tmux attach-detach behavior and Bitwarden
  authentication were not retested end-to-end.

## Deployment status

Source registration only. No live configuration files were
replaced during this repository import.

All new root deployment records use `deployed: false`.

## Rollback

Revert the scoped repository changes to restore the previous
source records. Existing live configurations are unchanged
by this import. Runtime `.zshrc` backups were created during
the earlier migrations and must be retained separately.
