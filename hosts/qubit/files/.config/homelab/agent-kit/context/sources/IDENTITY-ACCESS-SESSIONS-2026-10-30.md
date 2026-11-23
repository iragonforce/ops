# Session audit — configuration verified, lifecycle pending

The positive external Glance flow is verified by owner report and correlated edge/IdP/proxy records. This audit makes no new configuration changes.

| Layer | Observed configuration | What remains |
|---|---|---|
| authentik default passkey login | days=14; remember_me_offset seconds=0 | Actual browser cookie persistence, fresh passkey event and explicit logout/revocation behavior |
| authentik source login/enrollment stages | seconds=0 | Whether any source-based login is used in ordinary access; not the verified default passkey path |
| Cloudflare global | 336h | Browser restart/device restart and global-session expiry |
| Glance Access application | 336h; HttpOnly true; binding cookie true | Actual CF_Authorization expiry/flags and copied-cookie/device behavior |
| Glance Access policies | 336h for owner AND each specific provider | Real wrong-email denial; fallback account email compatibility |
| Main Stack app | 336h | Shared provider policy remains 730h and has its own duration; migration deferred |
| Shared Google/GitHub allow policy | 730h | Reused outside Main Stack; changing it affects several apps, so require a scoped change and recovery check |
| authentik proxy providers | Access token hours=1; refresh token days=30 | Actual token renewal, cookie persistence, reauthentication and revocation across apps |
| authentik OAuth2 providers | Access token minutes=5; refresh token days=30 | Per-consumer native app session and renewal behavior |
| Application-native login | Not audited | App-specific sessions, roles and logout propagation |

A one-hour forward-auth token is not evidence of a one-hour passkey prompt. A shorter token can renew or redirect through an existing IdP session. Likewise, the five-minute OIDC token does not determine the browser's full session lifetime. Do not extend all access tokens to 14 days merely to align numbers.

Observed Glance sequence at 2026-10-30 01:52 UTC: Cloudflare OIDC authorization and token exchange; forward-auth initial 401/start redirect; authentik Glance authorization and second token exchange; forward-auth 200 and dashboard 200. Owner reports no errors/loops. No evidence of an extra native Glance login was found. It is not known whether a second visible passkey prompt appeared.

The 14-day goal is configured at the IdP/global/pilot layers but not lifecycle-verified. Use an ordinary trusted browser profile for persistence testing: closing a private session normally clears its storage and is not proof of a session-configuration fault. Required client tests: browser restart and device restart; open another protected application; LAN/external transition; application token renewal; logout; targeted session revocation; loss/theft recovery. Do not revoke the owner's active working session while they are testing without coordination. No recurring job is required to claim configuration values; a real 14-day observation cannot be simulated by waiting in this task.

Next safe implementation: finish wrong-identity denial evidence; verify pilot cookie metadata and browser restart; inspect native sessions and classify services; then expand one exact-host owner/group policy at a time. Retain current recovery choices and independent SSH. Keep the shared wildcard's recovery paths until replacements are verified.

References: [Cloudflare session management](https://developers.cloudflare.com/cloudflare-one/access-controls/access-settings/session-management/) and [authentik proxy provider](https://docs.goauthentik.io/add-secure-apps/providers/proxy/). Cloudflare policy duration determines matched-policy token expiry; application duration supplies its default. Native application cookies remain a separate layer.
