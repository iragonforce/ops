# Infrastructure knowledge

Current source and change history: public `iragonforce/ops` (`consolidate`). Host checkout: `~/ops`. Main Nexus Hermes checkout: `/opt/data/workspace/ops`. Original private Hermes history and local work remain in `/opt/data/workspace/ops-private`, whose remote is `iragonforce/ops-private`; see `docs/changes/2026-11-23-hermes-public-ops-cutover.md`. Never merge private history into public `ops`.

Read the repository's `AGENTS.md`, then the relevant `docs/current`, `inventory/current.json`, and newest matching entry in `docs/changes`. Use `git log` and `rg` before repeating live discovery. `inventory/deployments.json` maps source to installed paths; `docs/workflow.md` explains guarded deployment and rollback.

Native Hermes `session_search` retrieves conversation context. The private Codex import ledger is `/opt/data/import-ledger/codex.json`; the older Paperclip archive remains a fallback. Historical claims need current source confirmation before promotion into current facts.

Legacy kit changelogs and context are dated evidence. Their original contents are preserved in Git history or private `iragonforce/backup`, branch `unified-infra-2026-11-06`. New meaningful outcomes belong in the ops repository, not another mirrored changelog. Use `docs/current/host-operations.md` for operating boundaries and preserve existing pending physical validations.

Specialist evaluation and current execution boundary: `docs/current/specialists.md`. The November 7 specialist pilot remains archived. As of November 8, Nexus Hermes native Kanban is the selected task system; Paperclip and its relays are retired, with historical data preserved. Hermes model inference is verified on Nexus and Tensor, but automatic specialist routing and recovery have not completed production acceptance tests. Do not activate autonomous specialist workers without a separately authorized, bounded test.

Finance Infrastructure current state, source provenance, import gates and recovery: `docs/current/finance.md`. Recent verified receipt and authenticated-mail intake: `docs/changes/2026-11-09-finance-receipt-sync.md` and `docs/changes/2026-11-09-finance-mail-intake.md`. Sensitive statement and transaction details stay in protected stores, not Git.

Nexus API gateway inventory, route/credential boundary and rollback pointer: `docs/current/api-gateway.md`; implementation history: `docs/changes/2026-11-09-nexus-api-gateway.md`. The Hermes API project and encrypted private GitHub backup branch hold the detailed 75-container/69-route catalog and recovery artifacts.
Nexus qBittorrent metrics, Grafana dashboards, source paths, verified limits and rollback: `docs/current/nexus-qbittorrent-monitoring.md`; evidence: `docs/changes/2026-11-13-nexus-qbittorrent-monitoring.md`.
