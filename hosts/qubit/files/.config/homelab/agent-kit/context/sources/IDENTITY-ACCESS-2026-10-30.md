# Identity and access: Phase 0/1 handoff — 2026-10-30 UTC

Status: Cloudflare IdP Test and the positive external Glance application flow are verified by owner report and correlated Cloudflare/authentik/NPM records. Different-email denial, browser cookie/persistence and full session lifecycle remain unverified. Phase 2/3 read-only inventory and session audits are saved; broader rollout remains incomplete. Owner performs browser tests personally.

## Live baseline

Execution was from the Paperclip container, through its existing strict-host-key SSH connection to Nexus. Nexus reports Debian 13. Existing sudo works. Qubit is reachable through Nexus's existing iragonforce SSH identity; the runner's direct Qubit identity was rejected and was not changed. Neither host's SSH configuration was changed. The capture helper is absent from the inspected noninteractive shells; diagnostics were filtered before output instead.

| Component | Live configuration |
|---|---|
| authentik server/worker | 2026.8.3, healthy; PostgreSQL 18 healthy |
| Nginx Proxy Manager | 2.16.0; nginx configuration check passed |
| cloudflared | 2026.10.0, running |
| Management | `/srv/containers/compose/infrastructure/compose.yaml` |
| proxy-backend | authentik 172.16.11.20; NPM 172.16.11.4; cloudflared 172.16.11.3 |
| authentik NPM route | ID 25, auth.blinkwired.com → authentik-server:30140; no forward auth |
| Grafana NPM route | ID 30, grafana.blinkwired.com → grafana:30037; local/network source restriction and authentik forward auth |
| authentik authentication | Default flow: order 10 blinkwired-passwordless-validation; order 20 default-authentication-login |
| WebAuthn validation | webauthn only, user verification required, deny if not configured |
| authentik session | days=14; remember_me_offset seconds=0 |
| Cloudflare global / Main Stack session | Both 336h; inherited allow policy still 730h (not aligned in this phase) |

The managed shared kit says AdGuard DNS is disabled and UDR7 supplies local split DNS. This supersedes the task's historical assumption that AdGuard currently supplies local DNS. No DNS changes were made or full client DNS audit performed.

## OIDC integration verified

Cloudflare account iragonforce (`b1a717c53611ecd6e8b84bd247ad46a1`), existing OpenID Connect provider `f9ea8365-c800-4e01-b146-7feb34b0bc7b`; authentik provider 42, Cloudflare-Access.

Both live client IDs are 40 characters with SHA-256 prefix `47e96bc16175e95b`. No client identifier or secret was changed. authentik has a nonempty confidential client secret; Cloudflare does not return its secret, so equality remains unverified pending a valid code exchange.

The callback is STRICT `https://iragonforce.cloudflareaccess.com/cdn-cgi/access/callback`; authorization flow is default-provider-authorization-implicit-consent. Provider authentication_flow is null; the existing default login flow remains in place. Both sides use the documented authorization/token/JWKS endpoints and openid/email/profile scopes; Cloudflare PKCE is enabled. The authentik signing certificate is RSA, valid 2026-02-04 through 2027-02-05. Public JWKS contains one RS256 signing key and parsed successfully as a public verification key.

Only akadmin has an enrolled WebAuthn device. Initially its email was root@example.com and roman's email was empty. The owner answered akadmin and offered iragonforce@pm.me or sergeyulanov@pm.me. The first address was chosen, consistently with the existing Cloudflare account email. After a fresh private backup and duplicate-email check, only akadmin.email was changed to iragonforce@pm.me; its active state and one passkey were read back. The actual existing email ScopeMapping now evaluates to that address with email_verified=false. No verification flag, password, passkey or other account field was changed.

## Changes and verification

1. Created a specific Cloudflare Access application for auth.blinkwired.com, ID `eb3957fe-ee93-4e41-bace-04e3051eaa4a`, with bypass policy `e7479d33-7e91-4ca3-882d-879e5e63b2e6`. This removes the recursive wildcard Access dependency from the identity provider hostname. authentik remains responsible for its login and administrative authorization. No other host is bypassed by this change.
2. Restored GitHub and Google to Main Stack's allowed identity-provider choices alongside OIDC, and set auto_redirect_to_identity=false. Before this change Main Stack selected only OIDC while its login-method allow rule recognized only GitHub/Google. Existing policy IDs/content were preserved. Its login page now displays all three choices. OIDC alone still does not satisfy Main Stack's existing provider-based allow rule; a separate narrowly authorized pilot is next after the identity question is answered. No global OIDC allow-everyone rule was added.
3. Saved fresh private identity backups and original Main Stack configuration on Nexus. No service was restarted, no passkey deleted, and no network/firewall/storage configuration changed.

Public probes used DNS-over-HTTPS plus an explicit Cloudflare destination IP and correct TLS SNI, bypassing LAN split DNS. These are public-edge checks from the runtime, not proof of an off-site browser login.

| Check | Before | After |
|---|---|---|
| Public authentik discovery | 302 to Cloudflare Access | 200 JSON, correct issuer and endpoints |
| Public JWKS | 302 to Cloudflare Access | 200 JSON, one usable RSA/RS256 verification key |
| Public login page | 302 to Cloudflare Access | authentik login shell returned |
| Invalid OAuth client/code | Not run | 400 invalid_client from authentik; no recursive redirect |
| Anonymous users/provider admin APIs | Not run | 403, no results |
| Anonymous public Grafana | Cloudflare Access gate | Still gated; no CF_Authorization observed |
| Main Stack fallback selection | Forced OIDC | Google, GitHub, OpenID Connect visible |

authentik events show akadmin authorized Cloudflare-Access at 00:21:20, 00:21:32, 00:22:00, 00:22:10 and 00:27:21 UTC before these changes. Those events do not prove a Cloudflare callback or application authorization. Bounded server logs since 00:00 (tail cap 6000) include seven authorize 302s, two authorize 400s, two token 200s and the diagnostic invalid-client 400. The 00:41:12 token 200 correlates with a Paperclip authorization and must not be attributed to Cloudflare. No redirect_uri_no_match was found in that bounded log capture. Access authentication-log API returned no rows for the queried period from October 28; no successful edge authorization can be claimed. NPM logs were checked in bounded, sanitized summaries, with no authenticated pilot session available to correlate.

## Architecture and remaining work

Public identity provider requests now follow Cloudflare TLS/Tunnel → NPM → authentik without an Access loop. Other wildcard services follow Cloudflare Access → Tunnel → NPM; Grafana additionally requires authentik forward auth and may then require its native login. Native application login has not been assessed. LAN/Tailscale paths should reach the intended private proxy and authentik controls; those client paths remain untested in this issue. SSH, NFS and SMB retain their existing independent protocol authentication and private transport controls.

Next owner: coordinator on this issue. Browser connection interaction `c6584bf4-e5db-4f9f-bcef-0da6d4c4f631` was cancelled at the owner’s request; the owner performs browser tests personally. Answered/applied owner identity question: `19d72671-d239-4d61-b9bb-b11554d0a812`. On continuation read their recorded outcomes; do not repeat the completed writes.

After the current token-exchange repair: have the owner use a fresh private external browser, perform Cloudflare's IdP Test with the owner's passkey, verify returned email/token verification, then create or reuse a Grafana-specific pilot policy restricted to that owner and OIDC. Preserve fallback recovery choices. Correlate the Access decision, authentik authorization, proxy requests and actual app content; inspect cookie presence and attributes without reporting values. Check a denied identity as well. Then assess duplicated prompts and proceed to session/application migration only after Phase 1 acceptance.

Remaining: Cloudflare IdP Test; actual external authorized/denied app tests; lifecycle/session revocation tests; full service inventory; browser trust design; hostname SSH; private NFS/SMB; client DNS/TLS comparison; hardening and complete recovery runbook. Main Stack has historical IP allow policies, WARP authentication enabled, a provider-wide Google/GitHub allow rule, HttpOnly false and binding-cookie false; record as deferred review items, not a completed security audit. No custom trusted-browser middleware was implemented.

## Backups and recovery

Nexus private backup directory: `/root/.local/state/authentik-backups/hom42-20261030T004456Z/`. Contains blueprint.yaml, authentik.dump (15,259,060 bytes, custom PostgreSQL format), globals.sql, compose.yaml, persisted-files.tar.gz, four private service environment files with private-env-map.json, and SHA256SUMS. The env files were copied from existing /etc/nexus/secrets/infrastructure paths into the root-only private-env directory; no values were printed. pg_restore --list passed with 1819 TOC lines. The certs/data/templates archive contains the three directories and no files at capture. The old 20261028 blueprint also exists. These files may contain private material and must stay private. This is a backup creation and structural validation, not a completed restore drill or off-host backup verification.

Cloudflare rollback snapshot: `/root/.local/state/hom42/mainstack-before.json` on Nexus. To undo the fallback-choice change, first re-read Main Stack, then restore only allowed_idps and auto_redirect_to_identity from that snapshot, preserving subsequent unrelated edits. Its previous state forces OIDC and can recreate the login problem, so use that rollback only deliberately. Delete only the specific auth application above to undo the recursion exception; doing so reintroduces the wildcard Access dependency. Preserve all existing application and shared-policy objects.

For authentik disaster recovery, preserve current data first, verify SHA256SUMS, and restore into an isolated PostgreSQL 18 database/volume using pg_restore with the saved globals and matching authentik 2026.8.3 images. Restore corresponding persisted bind content/config from the private snapshot, validate startup/flows/passkeys before routing production traffic, and retain the working deployment until acceptance. No production database restore or overwrite command was run. Do not treat blueprint import as a full database restore.

Operational recovery access was verified through independent SSH/sudo, which does not depend on Cloudflare or authentik. Emergency authentik recovery-key issuance was not exercised. Future credential rotation requires a coordinated replacement and rollback plan; no credentials were rotated here.

Reusable lesson: check the IdP hostname against wildcard Access coverage and compare application IdP selection with policy login-method selectors before debugging client credentials. Public discovery/JWKS reachability and authentik authorization events do not prove a successful Cloudflare login.

References: [Cloudflare authentik integration](https://developers.cloudflare.com/cloudflare-one/integrations/identity-providers/authentik-oidc/), [Access application path precedence](https://developers.cloudflare.com/cloudflare-one/access-controls/policies/app-paths/). Historical context consulted: Knowledge Home.md, Reference/START-HERE.md, Reference/09-open-issues.md and bounded history record 9164 (2026-03-21); older TrueNAS/SSH claims were treated as superseded. Existing October 18 secure-publishing report supplied prior route/rollback context and was checked against live NPM state.

Journal: `Changes/2026-10-29 204842 Repair recursive Cloudflare Access protection of authentik.md` was saved on Nexus. Its automatic Qubit copy reported unavailable; a manual transfer through the existing Nexus→Qubit SSH path succeeded and matched the source on readback. No note synchronization remains pending for this record. The canonical Qubit kit and Nexus mirror change records/context notes were also written and read back through that supported route.

## Continuation — owner identity applied (2026-10-30 01:29 UTC)

- Selected akadmin / iragonforce@pm.me from the owner-approved alternatives. Other offered address sergeyulanov@pm.me was not added as a second identity or claim. Scope evaluation confirms the selected email; this is not an authenticated browser token exchange.
- Fresh private backup: Nexus `/root/.local/state/authentik-backups/hom42-owner-20261030T012857Z/`, including database/globals, blueprint, persisted directories, Compose, four private env files and checksums. pg_restore --list passed with 1819 TOC lines; no restore drill.
- Targeted rollback snapshot: Nexus `/root/.local/state/hom42/owner-email-before.json`, also retained at `/root/owner-email-before.json` inside authentik-server. To roll back, re-read the account and restore only the saved prior email through the supported authentik user update or local ORM. Retain passkeys and unrelated fields.
- Existing auth-host exception, fallback choices and running versions rechecked. Public JWKS still parses as RSA; invalid client/code is rejected; anonymous users/provider APIs remain 403; Grafana remains Cloudflare-gated. No Cloudflare writes or service restarts in this continuation.
- [Staged Grafana pilot](/HOM/issues/HOM-42#document-pilot) is saved and read back. It requires exact owner email AND the specific identity provider in each policy, with 336h application/policy durations and Google/GitHub fallback choices. It is not deployed. No exact Grafana Access app existed at this live check. Re-read before creating one after the IdP Test. Recovery-provider email compatibility remains untested.
- Historical waiting posture superseded: owner will perform browser tests personally; hosted-browser request is cancelled. Current pending test is described below.
- Journal source: `Changes/2026-10-29 213024 Set authorized authentik owner email for Cloudflare pilot.md`. Automatic Qubit note synchronization failed; the supported Nexus→Qubit SSH fallback copied the note and matched the source on readback. No note synchronization remains pending.
- Reusable lesson: choose consistently among owner-approved email alternatives without another question, and preserve the actual email verification state.


## Continuation — token-exchange repair (2026-10-30 01:42 UTC)

Owner reported successful authentik login in a private window followed by `OIDC ERROR: Failed to exchange code for token. Make sure the client secret is correct.` This proves neither Cloudflare identity acceptance nor a complete fresh passkey challenge. Bounded authentik logs identify `Invalid client secret` and token HTTP 400 at 01:38:56 UTC, request `ca24d2ee9bc047909e8022af37ab76ef`.

The provider is still 42, confidential; its existing secret is a 128-character plaintext value compared directly by installed authentik 2026.8.3 code. Client ID fingerprint still matches `47e96bc16175e95b`. A local request using this secret with an intentionally invalid code returned `invalid_grant`, demonstrating successful client authentication.

Reapplied only that same existing secret to existing Cloudflare provider `f9ea8365-c800-4e01-b146-7feb34b0bc7b` at 01:42:46 UTC through the supported Qubit SSH/API path. The connected Cloudflare tool has no private host-secret transfer mechanism. Credentials traveled in subprocess memory/SSH stdin, not chat, command arguments or new files. No rotation, authentik write, passkey edit, restart, policy or application edit occurred. API write succeeded; subsequent readback confirmed unchanged non-secret provider configuration, other providers and all Access applications.

Public-edge probes with explicit public DNS destination and TLS SNI: existing valid client secret plus intentionally invalid code → HTTP 400 `invalid_grant`; invalid secret plus same invalid code → HTTP 400 `invalid_client`. These establish token-endpoint client authentication and denial behavior, not a successful real code exchange. Do not claim end-to-end success until the owner runs a NEW Test and reports expected email `iragonforce@pm.me`. Do not reuse the prior callback URL or refresh its error page. The Grafana pilot remains staged.

Private recovery references: Qubit `/Users/iragonforce/.local/state/hom42/cf-secret-reapply-20261030T014245Z/` stores returned API before-state; Nexus `/root/.local/state/hom42/cf-secret-reapply-receipt.json` stores sanitized acceptance/readback receipt. Cloudflare does not return the old secret, so the snapshot cannot restore that unknown old value. The existing authentik secret remains unchanged and authoritative for repair/reapply. Restore only affected non-secret fields from snapshots if required, retaining later unrelated edits. Prior authentik backups remain unchanged; independent SSH/sudo works.

Journal: `Changes/2026-10-29 214321 Repair Cloudflare OIDC client secret mismatch.md` saved on Nexus; automatic Qubit copy failed; supported Nexus→Qubit SSH fallback copied the note and matched it on readback. No note synchronization remains pending. Owner-result interaction replaces the cancelled hosted-browser gate. Remaining: fresh IdP Test; pilot backend and policy checks before deployment; real external authorized/denied access, cookie/log correlation and all broader phases. Reusable lesson: distinguish invalid client authentication from invalid authorization grants using correlated IdP logs and a deliberately invalid code.


## Continuation — successful IdP Test and deployed Glance pilot (2026-10-30)

Owner's answered retest at 01:46:48 UTC returned email iragonforce@pm.me, oidc_fields {}, amr [user] and “identity provider works”. This satisfies owner-observed IdP Test success and returned email. authentik token HTTP 200 at 01:46:26.238066, request 1def7e22db074b8380628ed7901e1038, correlates with it. Fresh passkey use still needs explicit confirmation; amr [user] does not attest WebAuthn specifically. Interrupted run 2406ab24-4584-47e6-8da5-7d23ba86ab3d failed at model capacity; this continuation checked live state before mutations and did not replay the completed secret repair.

Grafana and Prometheus are stopped (exit 0 nine days ago). Grafana NPM host 30 also requires private administrative source networks. Preserved these services/controls and selected active Glance at glance.blinkwired.com; the original Grafana template is superseded, not an instruction to deploy later automatically. Glance / and /api/healthz return 200 from NPM, title Home. NPM host 198 routes to glance:8080 with existing authentik forward auth, provider 5/application blinkwired-glance. akadmin is active, superuser and belongs to authentik Admins, allowed by its existing binding. No app/IdP/origin auth policy, proxy, tunnel or DNS changed.

Deployed exact-host Access application 2b679108-2860-48e4-b10c-eeee739d8b67 with three owner-email AND provider policies. OIDC policy ece142ac-14b7-4c75-9a95-519d70b8e7da; Google a393db30-0955-4aab-9d21-b3e9bfc9d038; GitHub d65d1613-6a5e-408c-92c6-b752342f0cf4. Application and policies 336h; HttpOnly/binding cookies enabled; WARP authentication and automatic redirect off. Existing Google/GitHub choices retained; their actual account email compatibility untested. All other Access apps matched pre-change snapshots. No service restarted.

Anonymous and forged identity-header probes through explicit public-edge DNS/TLS both return 302 to Cloudflare login for glance.blinkwired.com. They do not prove denial of a different authenticated identity. Access log query since 01:44 UTC returned no rows at this check. Actual valid pilot session, identity, CF_Authorization presence/expiry, forward-auth behavior, dashboard content and denied-identity session remain pending. [Pilot instructions and recovery](/HOM/issues/HOM-42#document-pilot).

Rollback: delete only Access application 2b679108-2860-48e4-b10c-eeee739d8b67, returning this hostname to unchanged Main Stack wildcard. Do not modify shared policies or other apps. Nexus state: /root/.local/state/hom42/apps-before-glance.json, glance-pilot.json and glance-created.json. Independent SSH/sudo remains available. Earlier backups and secret-repair recovery references above remain valid.

Journal Changes/2026-10-29 215105 Verify Cloudflare IdP test and deploy Glance owner pilot.md saved on Nexus. Automatic Qubit sync failed; manual supported Nexus→Qubit SSH fallback copied the note and matched on readback. No journal synchronization remains pending. Coordinator owns the pending external browser test, then correlates logs before Phase 1 acceptance. All broader phases remain incomplete. Reusable lesson: select a running representative application and inspect origin restrictions before adding edge enforcement.


## Continuation — positive real-application flow verified (2026-10-30 01:52 UTC)

Owner answered at 01:52:44 UTC: “It was done and it was succesful, no error or loops”. Accept this as successful instructed Glance test with no errors/loops; it does not separately document every optional cookie/alternate-identity detail.

Correlated server evidence:

| UTC | Layer | Evidence |
|---|---|---|
| 01:52:10 | Cloudflare Access | app 2b679108-2860-48e4-b10c-eeee739d8b67, glance.blinkwired.com, user_email iragonforce@pm.me, connection oidc, allowed=true, action login, ray a526c771bc74ac28 |
| 01:52:10.293598 | authentik | akadmin authorized Cloudflare-Access, event 2c587c68-a0dd-455e-b481-916a104537a1 |
| 01:52:11.023104 | authentik | token HTTP 200, request 5ccd33a6c98a476abad9b3e8881e2be1 |
| 01:52:12 | forward auth / NPM | initial auth 401 and outpost start redirect |
| 01:52:17.927092 | authentik | akadmin authorized glance.blinkwired.com, event 9d789346-3dcb-4820-97ea-b59e8a72c8eb |
| 01:52:18.076957 | authentik | second token HTTP 200, request 31814d90935f4f7e81d88ee54aa08caf |
| 01:52:18 | forward auth / NPM | auth 200; root, static assets and /api/pages/home/content/ all upstream/proxy 200 |

NPM dates carry -0400 and were normalized to UTC. Outpost logs also display local time; Python authentik logs/events are UTC. Do not count the four-hour presentation difference as a second session or clock fault. The allowed event is for this exact pilot; only its OIDC policy matches email+OIDC. Cloudflare did not return a separate policy-ID field, so policy identity is inferred from verified configuration, not directly logged. Both edge OIDC and origin forward-auth layers executed. No native Glance account login was observed. Owner reports no loop; number of visible prompts was not separately specified.

No repeated login request is needed. The different-email negative test and actual CF_Authorization metadata/lifecycle are still unverified. Saved narrow result question f410daf3-273e-434e-856c-e4bd8bdd1ea0 asks only whether the distinct alternate-account test was denied or not tested; coordinator retains ownership. Anonymous and forged-header checks already passed but are not equivalent to a wrong-email session.

Independent progress: captured 69 containers (59 running), 39 NPM hosts, 34 forward-auth hosts, seven private-source-restricted hosts and 36 authentik applications. [Initial inventory](/HOM/issues/HOM-42#document-inventory) maps observed routes, backend state, bindings and edge matches; DNS/native OIDC/application privileges remain unassessed. [Session audit](/HOM/issues/HOM-42#document-sessions) records authentik days=14, Cloudflare global/pilot 336h, shared policy 730h, proxy access tokens hours=1 and refresh days=30, OAuth2 access minutes=5/refresh days=30. No live authentication/session setting changed. Avoid replacing all short tokens with 14-day tokens: renewal and browser sessions are separate. Persistence tests require a normal trusted profile; closed private sessions normally discard state.

Rollback remains delete only pilot 2b679108-2860-48e4-b10c-eeee739d8b67; no new configuration change in this continuation. All broader architecture/client/native protocol work remains incomplete. Reusable lesson: correlate edge decision, both IdP authorizations, token exchanges and actual backend content, accounting for source timezones.

Tool proposal from repeated observed friction: add a narrowly scoped Knowledge retry_note_sync(path) operation for existing change notes only, allowlisted Nexus source and Qubit vault destination, returning copy/readback checksum or pending status. Estimated savings: replace roughly two manual SSH copy/readback operations per failed automatic note sync; no measured token saving is claimed. It must not accept arbitrary source/destination paths or credentials. This is a proposal only; no tool installed or access widened.

Journal for this verification: Changes/2026-10-29 215706 Verify Glance OIDC access and audit session layers.md. Automatic Qubit copy failed; supported SSH fallback matched on readback. Canonical kit source supplements: IDENTITY-ACCESS-INVENTORY-2026-10-30.md and IDENTITY-ACCESS-SESSIONS-2026-10-30.md.
