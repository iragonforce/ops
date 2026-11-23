# Finance encrypted backup baseline — partial recovery verified

Date: 2026-11-09. Objective: provision an owner-authorized backup encryption key in the existing Bitwarden Secrets Manager infrastructure project, create non-disruptive encrypted Nexus finance snapshots, and validate isolated recovery without touching production databases.

## Scope and key custody

The owner selected a **new dedicated key in existing Bitwarden Secrets Manager**. The approved infrastructure project was resolved by ID and name. The official Bitwarden Python SDK 2.1.0 was installed only in the Hermes scratch area for this one-time bootstrap; its access-token login used the existing TPM-sealed BWS service credential, not a new login or persistent token file. A 256-bit random passphrase was generated in memory and created as `FINANCE_BACKUP_GPG_PASSPHRASE_V1`, reference `b54c9237-9091-408d-9ff7-b4fd00665d81`. The new key never appeared in process arguments, logs, Git, board comments or agent output. Independent `bws secret get` compared its value in memory to the generated value, and project-scoped `bws secret list` confirmed the exact key in `infrastructure` after an initial readback-shape mismatch (`projectId`, not `projectIds`). No duplicate secret was created.

**Recovery boundary:** this check used Nexus's TPM bootstrap and does not prove that the owner can retrieve the secret through Bitwarden independently if Nexus is unavailable. The owner must verify the secret is visible in their Bitwarden Secrets Manager access (do not share its value in chat) before any GitHub upload or off-host recovery claim. The temporary SDK target in Hermes scratch is not an operational dependency; normal retrieval uses the existing `bws` CLI.

## Actual backup

Nexus has GnuPG 2.4.7 with AES256; no new persistent encryption package, script, job, database or service was added. A synthetic plaintext encrypt/decrypt roundtrip verified GPG operation with the Bitwarden passphrase delivered over an inherited file descriptor, not the CLI argument vector. For real data, `pg_dump -Fc` and `tar` streamed directly into GPG AES256 symmetric encryption with restrictive umask; no plaintext dump was written to disk or printed.

Protected Nexus-host destination: `/var/backups/homelab/finance/baseline-2026-11-09`, mode 0700; artifacts, `manifest.json` and `verification.json` are mode 0600. Five encrypted files total 657,025,761 bytes:

- `receipt-wrangler-pg17.dump.gpg` — PostgreSQL 17 consistent dump.
- `finance-analytics-pg17.dump.gpg` — existing finance analytics PostgreSQL 17 consistent dump.
- `n8n-pg18.dump.gpg` — PostgreSQL 18 consistent dump, including workflow and database-stored credentials/settings.
- `receipt-wrangler-files.tar.gpg` — current persistent files directory (no regular files at capture time).
- `n8n-files.tar.gpg` — current n8n persistent files, including config; approximately 656 MB, too large for routine Git snapshots without an explicit size/retention design.

The file archives were streamed from running applications. Their individual tar integrity is checked, but cross-file application consistency is **not** proven. `manifest.json` records SHA-256, byte size, encryption/key reference and scope; `verification.json` records tests and unresolved criteria. No artifact was uploaded to GitHub. Existing scheduler/configuration and all application data paths were left unchanged.

## Verification

- Five artifact SHA-256 values matched `manifest.json` at creation and during the verification readback.
- Both PostgreSQL 17 dumps were decrypted and restored into separate databases in a temporary `postgres:17-alpine` container with `--network none`. Restored Receipt Wrangler counts were one receipt/two items; restored analytics counts were 16 purchase receipts/73 receipt items/zero transaction matches, matching the pre-backup live aggregates. The first startup `createdb` check raced PostgreSQL initialization; a bounded readiness retry succeeded. The temporary container was removed.
- The n8n dump was decrypted and restored into a temporary `postgres:18-trixie` container with `--network none`; its restored database contained six workflows, three active, matching the live aggregate. The temporary container was removed.
- The encrypted receipt and n8n tar streams were fully decrypted and parsed in memory. Receipt archive: two directory members, zero regular files. n8n archive: 9,546 members, 9,527 regular files, 648,525,947 plaintext bytes read, config member present. No plaintext archive extraction or application login was tested.
- Production containers were neither stopped nor altered. Temporary restore containers were removed. The protected verification metadata readback passed with mode 0600.

## Unresolved / stop conditions

**Wealthfolio remains unbacked-up by this task.** Its v3.12.0 upstream self-host backup guide (`docs/self-host/backups.md` at the matching release) recommends taking a snapshot and password-protected `.wfbackup` export through the authenticated Backup & Export UI. The web route reached Authentik/Cloudflare Access sign-in, so no authenticated export occurred. Raw copies of its six live database files/WAL are not an application-consistent substitute and an original encrypted snapshot also needs the original server master key. Do not stop it for a raw archive without coordination; no isolated Wealthfolio restore is claimed. Its finance imports remain blocked.

Independent owner-side Bitwarden key retrieval, an off-host copy and restore, n8n application-level file recovery, backup retention, ongoing scheduling, and artifact size policy remain unverified. Specifically, the 656 MB encrypted n8n file archive was **not** pushed to the private GitHub repository. No new executable was deployed under the required Nexus-host `/opt/data/bin` (which still does not exist); one-time operations ran in ephemeral tooling.

## Rollback and records

No production finance state changed. Retain the new Bitwarden key while any artifact uses it; deleting or rotating it without re-encryption would make those backups unreadable. Keep the protected baseline until a replacement has passed equivalent verification. The exact protected directory can be removed only after retention review, not as automatic cleanup. Non-secret docs are owned by `iragonforce/ops`; revert only their containing revision if needed, leaving the independent backup and vault reference intact. Board `finance-infrastructure` backup/restore card stays blocked until Wealthfolio and independent recovery gates pass. The containing Git revision is discoverable with `git log --follow -- docs/changes/2026-11-09-finance-backup-baseline.md`.
