# Paperclip → Hermes preparation — 2026-10-17

## Verified state

- Paperclip runs separately from Hermes on Nexus. Its UI is `http://192.168.4.20:3100`, organization homelab. The UI showed only the existing coordinator agent; no Hermes agent was present.
- Both containers already share the private paperclip-hermes Docker network. Hermes's authenticated API responds at its API root (`/health` and `/v1/models`); adding `/api` to that API endpoint returns 404.
- The supported adapter is `hermes_gateway`. `hermes_local` would launch a local CLI rather than use the existing independent runtime.
- Installed Paperclip gateway validation rejects non-loopback plain HTTP unless its insecure escape hatch is enabled. That escape hatch was not enabled.
- No saved organization Hermes API secret was visible in the selection list. The new agent form was prepared as Hermes / Hermes Gateway with base URL `http://127.0.0.1:18642`.

## Completed preparation

Added `hermes-api-relay` to `/srv/containers/compose/paperclip/compose.yaml`, project stack. Container `paperclip-hermes-relay` shares Paperclip's network namespace and binds only 127.0.0.1:18642, forwarding to Hermes's existing API over their pre-existing same-host Docker bridge. No host port, public endpoint, firewall opening or insecure-HTTP override was added. API bearer authentication is still required.

The relay uses the existing pinned Paperclip image, UID 10000, read-only filesystem/script, dropped capabilities, no-new-privileges, bounded logs, health check and restart policy. Dependency restart propagation follows Paperclip when Compose restarts/recreates it. Source: `/srv/containers/compose/paperclip/hermes-api-relay.mjs`.

Paperclip and Hermes were not restarted. The relay reports healthy. The installed adapter's actual `testEnvironment` connection check returned pass, including loopback transport allowed and authenticated gateway health reachable. The API key stayed in process memory and was not printed. No model inference, task assignment, routine or external message was started.

## Pending final action

The agent has NOT been created, and no API key has been saved to Paperclip. Browser automation requires action-time confirmation before granting an agent/app security-sensitive access. The next action is to store Hermes's existing API_SERVER_KEY as a Paperclip organization secret and finish creating the prepared Hermes Gateway agent. This permits Paperclip to invoke Hermes's configured tools. Do not confuse preparation with completed registration or an end-to-end model run.

## Rollback

Private before-state: `/srv/containers/data/paperclip/recovery/hermes-gateway-20261017-183807/compose.yaml` and ROLLBACK.md. Stop/remove only hermes-api-relay using project stack and this Compose file; compare later edits before restoring the compose before-state. Existing database, model/provider credentials, Hermes configuration and human browser session were not changed. Once the agent is created, revoke its specific adapter secret/agent separately if withdrawing integration.

## Sources

- Installed `/app/packages/adapters/hermes/src/gateway/server/test.ts` and gateway package source.
- Official adapter documentation: https://github.com/paperclipai/paperclip/blob/master/packages/adapters/hermes/README.md
- Official gateway guide: https://github.com/paperclipai/paperclip-docs/blob/main/docs/reference/adapters/hermes-gateway.md

## Completion update — 2026-10-17

The user approved saving the existing key and creating the agent. Registration is now completed; the earlier pending section describes the initial preparation state.

- Created encrypted organization secret `Hermes Gateway API`, key `hermes-gateway-api`, reference `1d088cb8-b068-40a8-8796-1694f9d7d375`. The existing Hermes key was reused, not rotated. Temporary private staging was removed immediately after form entry.
- Created and approved agent `Hermes`, ID `ea829891-5ec7-4080-999f-1966317644da`, adapter hermes_gateway, role general. Approval `4454c6c9-48b5-41ab-8816-273f94f32072` is approved. The UI showed the agent idle and no runs.
- Gateway URL is `http://127.0.0.1:18642`; its key field uses the stored secret reference. Callback URL is `http://paperclip:3100`, verified reachable from Hermes. Added instructions to read current AGENTS.md and homelab context and work only on the current assigned task.
- Heartbeat on interval remains OFF; no new routine, task assignment or agent run was started. Adapter connection check passed again after Paperclip recreation. No inference or formal tests were performed.
- Paperclip's automatic key-storage helper failed on plain HTTP with `crypto.randomUUID is not a function`. Saved the key through the supported named-secret screen and selected it in the agent form; no vendor source patch was made.

### Tailscale HTTPS

User permitted Tailscale HTTPS or Cloudflare service exposure. Configured private Tailscale Serve at `https://nexus.tail4e4f0f.ts.net:9443`, forwarding to Paperclip. Funnel/public exposure was not enabled. Requests from Qubit to the app and health endpoint returned HTTP 200 with certificate verification. Browser displayed the normal Paperclip sign-in page at this new origin; authenticated login at that origin was not performed. Sign in again using the existing account.

Paperclip used environment-only configuration; its configured config.json did not exist. Added exact allowed hostnames for the tailnet name, Docker callback name, existing LAN access and future paperclip.blinkwired.com. Set its public URL to the new HTTPS origin. Both agents were observed idle before briefly recreating Paperclip and its namespace-sharing relay. Hermes itself was not restarted. The relay recovered healthy and the gateway check passed.

HTTPS recovery: `/srv/containers/data/paperclip/recovery/https-host-20261017-184709`. Tailscale Serve before-state and single-listener rollback: `/var/lib/nexus/service-access/recovery/paperclip-https-20261017-184549`. Remove only 9443 using `tailscale serve --https=9443 off`; compare later edits before restoring compose. This recreates Paperclip, so coordinate active work first.

### Custom domain status and pending work

Public DNS for nexus.blinkwired.com and paperclip.blinkwired.com returned Cloudflare's 172.64.80.1. HTTPS probes forced to that public address redirected to iragonforce.cloudflareaccess.com. This verifies the Access entry point, not Access login or working application routing. No matching NPM proxy host was found for either service. Local split DNS returned the existing Nexus LAN mapping and must not be mistaken for public DNS validation.

No Cloudflare routes, DNS records or Access policies were changed. Custom-domain application routing remains pending private Cloudflare management credentials and service-specific setup. Credentials must be supplied by private file path, not pasted into chat. Preserve existing Access protection.


## 2026-10-17 — Paperclip runner API and separate Tensor Ollama agent

- Corrected `PAPERCLIP_API_URL` to `http://paperclip:3100` in Nexus `/srv/containers/compose/paperclip/compose.yaml`. Docker runners could not reach the browser Tailscale URL. Browser `PAPERCLIP_PUBLIC_URL` remains `https://nexus.tail4e4f0f.ts.net:9443`. Recreated idle Paperclip and its loopback Hermes relay only.
- Created and approved **Tensor Ollama**, ID `0e56606c-6ecf-4047-8fd7-e6eee1b3ca09`, using `opencode_local`, model `ollama_tensor/gpt-oss:20b-64k`, existing Tensor Ollama endpoint, and persistent runner workspace `/paperclip/workspaces/tensor-ollama` (host `/srv/containers/data/paperclip/workspaces/tensor-ollama`). Reports to coordinator. Timer heartbeat off, on-demand wake on; agent/skill creation permissions off.
- Hermes remains on its existing Codex configuration; its adapter configuration fingerprint was unchanged. No Tensor installation, model download or inference was performed in this maintenance step.
- Used the installed application's board-auth service to issue a five-minute maintenance credential for the existing administrator, then submitted the hire/approval through normal REST APIs. Credential stayed in process memory and was revoked in finally; revocation independently verified. Coordinator privileges and authentication mode were unchanged.
- Operational checks: internal API health HTTP 200; normal authenticated hire and approval succeeded; Tensor model catalog reachable from Paperclip; OpenCode recognizes the exact configured provider/model; workspace owned by UID 1000; agent idle. First actual Paperclip inference task and subsequent wake remain pending. An initial direct OpenCode probe incorrectly passed normalized environment objects; rerunning with their plain values succeeded, requiring no configuration change.
- Rollback before changes: `/srv/containers/data/paperclip/recovery/runner-api-20261017-191804` contains prior Compose configuration. `/srv/containers/data/paperclip/recovery/tensor-ollama-20261017` contains prior agent records, hire payload/result, verification and rollback notes. Pause the new agent before rollback and check for assigned work; preserve audit history and workspace.
- Existing public custom-domain routing remains pending. Private board URL: https://nexus.tail4e4f0f.ts.net:9443 .


## 2026-10-17 — Paperclip UI instruction editing

- Confirmed the existing user account already has `instance_admin`; no privileges or authentication settings were changed.
- Migrated Tensor Ollama's external host instructions and Hermes's inline instructions into managed Paperclip bundles through supported board APIs. Coordinator was already managed and retained its content. All three now use managed instructions.
- Preserved original entry content, external source files and existing instruction candidates. Seeded Hermes's managed entry from its original inline instructions because the generic bundle exporter does not read that adapter's inline `instructions` field.
- Verified managed revision commits and read-back content equality for Hermes and Tensor Ollama. Models, provider credentials, networks and services were not changed or restarted. UI-only/browser rendering was not rechecked; copy unsaved editor text before reloading, then retry saving. Existing drafts/candidates were not automatically applied.
- Used short-lived local maintenance credentials for the existing admin, revoked in finally on every attempt. Initial probes stopped on revision-token shape and external candidate-list restrictions; the final normal commit used the current revision ID and succeeded.
- Private backup, prior configuration, original entry copies, candidate records and rollback: Nexus `/srv/containers/data/paperclip/recovery/managed-instructions-20261017`. Restore prior instruction config fields through the board API only after checking current edits/runs; retain managed revision history.
- Instance-admin access covers supported Paperclip UI settings. Host OS/Docker configuration and fields not exposed by Paperclip still require host administration.
