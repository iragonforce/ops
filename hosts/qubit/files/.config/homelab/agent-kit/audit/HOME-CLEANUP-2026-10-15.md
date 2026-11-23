# Tensor and Nexus home artifact cleanup — 2026-10-15

## Scope and result

At the user's request, cleaned only loose top-level `.py` and `.md` files in `/home/iragonforce` on Tensor and Nexus. These were dated setup, migration, verification scripts and historical implementation reports. Authorship cannot be established from filenames alone; files were classified by observed purpose and runtime references, not asserted Codex provenance.

- Tensor: archived 13 Python files and 2 Markdown reports; preserved `AGENTS.md` in place.
- Nexus: archived 82 Python files and 15 Markdown reports; no loose top-level Python/Markdown files remain.
- No recursive project, hidden configuration, credential, pool or application-data cleanup was performed. No files were permanently deleted. Historical reports remain intact in the private archives.

## Checks

Audited systemd units, cron locations, shell startup files, installed local tools, user services, Hyprland/autostart configuration, symlinks and live processes. Privileged audit completed with no unreadable paths in the selected runtime scope. No live direct references to the removed home paths were found. Same-name references to telemetry resolve to `/usr/local/libexec/homelab-telemetry.py`, not the loose copy. Identical installed copies of maintained runtime tools were checksum-checked. Container bind sources were checked against candidate paths before moves.

All archived files were verified against pre-move SHA256 values, and absence at original paths was checked again after the operation. Systemd active states and Docker container ID inventories were unchanged before/after. Telemetry, NFS and Tailscale remained active on both hosts; Tensor's existing NFS recovery timer remained active. Nothing was restarted. This is a scoped operational check, not a full audit or proof of all service behavior.

The first Nexus cleanup attempt stopped before moving anything because an installed script was root-readable only. Repeated installed-copy verification with privileged `sha256sum`, then completed the cleanup normally.

## Rollback

Update, 2026-10-15: the user explicitly requested permanent removal after cleanup. Deleted both archives listed below, including all 15 Tensor and 97 Nexus archived files and their manifests. Verified both archive paths absent. The archive-based rollback described below is no longer available. Installed tools and retained home files were not changed. This was ordinary filesystem deletion, not secure erasure or removal of independent backups/snapshots.

Private archives, each with original filenames and `manifest.json` checksums:

- Tensor: `/home/iragonforce/.local/state/home-cleanup/20261015-215603/`
- Nexus: `/home/iragonforce/.local/state/home-cleanup/20261015-215617/`

Restore only desired files to `/home/iragonforce/<original-name>`, refusing to overwrite an existing file. The manifest lists exactly which files moved and their checksums. Do not run archived installers to restore the files: those installers can change services and represent superseded state.

Audit tooling/reports live under each host's private `~/.local/state/home-cleanup-audit/`, not in the home root. Installed service tools and the shared agent kit remain in their maintained locations. Canonical full kit mirror sync remains pending; no unrelated runtime deployment was triggered.
