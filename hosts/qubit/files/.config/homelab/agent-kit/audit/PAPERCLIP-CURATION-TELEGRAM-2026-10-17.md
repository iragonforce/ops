# Paperclip skill curation and Telegram

2026-10-17, America/Toronto.

## Correction and audit scope

The initial migration imported 1,146 packages as references. It deduplicated exact original skill documents but did not individually audit every skill or establish runtime necessity. That was excessive for the active library.

Screened all imported packages for provenance, version/name duplication, runtime portability, client-specific tooling, installation commands, credential references, autonomous delegation and mandatory-test instructions. Screening found 177 duplicate-name groups. Pattern flags are triage, not proof of malicious behavior. Archived scripts were not executed or exhaustively security-reviewed.

Removed 1,143 unused imported skills through Paperclip's supported API; all removals returned 200. Refreshed library contains **11** skills:

- Three reviewed local skills: homelab history retrieval, change journal, token efficiency.
- Eight built-in Paperclip skills: paperclip, paperclip-board, paperclip-converting-plans-to-tasks, paperclip-create-agent, para-memory-files, first-task, slack, agentmail. Bundled Slack/AgentMail remain unassigned. Built-ins are maintained by the installed application.

Existing assignments remain: coordinator nine, Hermes three, Tensor Ollama four. Hermes gateway still does not implement native skill sync; its three focused compatibility copies remain. Original source packages, import metadata, transcripts and history index remain intact. Re-import selected packages only for an actual task after reviewing their instructions/resources.

Private per-package decisions and rollback references: `/srv/containers/data/paperclip/migrations/20261017/private/skills-curation-audit.json`. Original metadata: `import-skills-results.json` in that directory. Source packages: `/srv/containers/data/paperclip/migrations/20261017/public/skills`.

## Telegram

Reused the existing token from `/etc/nexus/secrets/telegram/runtime.env`, verified with Telegram getMe. Bot: `@iragonforce_bot`. No token value was displayed or copied to Qubit. The old `tg-bot` was an OpenClaw polling relay. Paperclip now owns inbound updates; the bot's outbound REST service remains at the same address. Boot notification callers were not changed.

Prepared a derivative of the existing pinned bot image adding `TELEGRAM_POLLING=false`; preserved original source, image and Compose files. No dependencies were upgraded. Recreated only Paperclip, its relay and tg-bot. Hermes and the knowledge service remained running.

Native Paperclip connection **Homelab Telegram** is assigned to coordinator. Only direct messages are allowed; unlinked people and group chats are disabled. The bot token was supplied in memory to the supported setup API and persisted by Paperclip's encrypted credential store.

Published only the Telegram webhook through Cloudflare at `paperclip-chat.blinkwired.com`, with a specific Access bypass for `/api/chat-webhooks` and a tunnel path rule restricted to Telegram webhook URLs. Existing wildcard UI Access protection remains. Public-edge checks: unknown endpoint 404, actual unsigned endpoint 401, protected UI 302 to Access. Local split DNS requires public-edge resolution for these checks.

Telegram getWebhookInfo reported the correct public host, no pending updates and no last delivery error. Paperclip is **verifying / test**, pending a genuine user message, owner identity linking and native qualification. No message or sender identity was fabricated. No model conversation was claimed verified.

## Operational checks and rollback

- Active library refreshed to 11; all desired skill assignments retained.
- Paperclip running; Paperclip relay, knowledge service and tg-bot healthy.
- Notification REST `/commands` returned 200. No external test message was sent.
- Telegram webhook registered; actual public unsigned endpoint rejects with 401.
- Original skill source existence checked after removal; full archives retained.
- No formal tests, scheduled jobs or Siri Shortcuts were created.

Final check just after midnight on 2026-10-18 found the staged `public` root denied UID 10000 traversal despite the Obsidian subtree ACLs. Saved the prior root ACL and granted only `u:10000:rx` at that root, then refreshed the knowledge catalog/health. `record_change` succeeded through the Paperclip broker and synchronized its linked note to Qubit. Rollback ACL: `public-root-acl-before.txt` in the Telegram recovery directory; restore with `setfacl --restore=<private-path>` if reverting. Existing Hermes unsupported skill-sync warning and OpenCode's shared Claude skills-home notice remain intentional.

Nexus rollback: `/srv/containers/data/paperclip/recovery/telegram-paperclip-20261017/ROLLBACK.md`. Remove/disable Paperclip's webhook before re-enabling old tg-bot polling; restore saved matching Compose/source/image. Cloudflare before-state and created object IDs: Qubit `~/.local/state/paperclip-integration/telegram-20261017`. Restore the saved tunnel config and remove only the new webhook DNS/Access objects. Do not change Main Stack policies.
