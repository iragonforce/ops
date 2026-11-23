# Local HTTPS recovery — 2026-10-23 (America/Toronto)

Execution: Hermes in Nexus Docker; Nexus host changes through the Paperclip SSH path. This is a dated follow-up to `LOCAL-HTTPS-2026-10-19.md`.

## Change

The NPM leaf certificates for `paperclip.homelab.lan`, `hermes.homelab.lan`, and `nexus.homelab.lan` had expired on 2026-10-20. Renewal had previously failed because the host-network renewal client could not resolve `ca.homelab.lan`; after that DNS issue was corrected, `step ca renew` correctly refused the expired certificates.

Preserved the existing step-ca root identity. The step-ca Compose service now has host entries for `paperclip.homelab.lan` and `hermes.homelab.lan` resolving to NPM's fixed `proxy-backend` address `172.16.11.4`, so the ACME HTTP-01 validator can reach the shared NPM webroot despite Docker's external-only resolver. Recreated only the `step-ca` container. Its health returned `ok` and the root fingerprint remained `d177228fbc6735a2b3c1d965b687d1097ef56dbafae0bcd07cc4012b8f90cc2b`.

Issued new Paperclip and Hermes leaves through the existing step-ca ACME directory and NPM webroot; reissued the Nexus leaf through the existing `admin` JWK provisioner. Verified each hostname and chain against the existing root/intermediate, verified the certificate/private-key public key pairs match, and built each fullchain from leaf plus intermediate. Installed only the three per-host certificate sets with owner UID/GID 568 and mode 0600. NPM `nginx -t` passed and Nginx was gracefully reloaded; the NPM container itself was not restarted.

Updated `/srv/containers/compose/step-ca/renew-nginx-homelab.sh` to add `ca.homelab.lan:192.168.1.2` to the host-network renewal client. A manual `homelab-stepca-renew.service` run then completed successfully and skipped all three leaves because each had about 23h56m remaining. The four-hour timer remains active; its next check was scheduled for 2026-10-23 20:22 EDT. Actual unattended certificate rotation has not yet been observed.

## Verification

- A temporary HTTP-01 token was fetched successfully from the actual step-ca container for both Paperclip and Hermes hostnames, then removed.
- Paperclip-container curl to `https://hermes.homelab.lan/health`: HTTP 200, TLS verification result 0.
- Paperclip-container Node HTTPS request to the same endpoint: HTTP 200 with normal certificate verification.
- Paperclip UI route from Tensor on the LAN: HTTP 200, TLS verification result 0.
- The same Paperclip UI request from the Paperclip container returned HTTP 403 with TLS verification result 0 because that container is outside the NPM LAN allowlist; the access policy was not changed.
- Live SNI checks served the newly issued Paperclip, Hermes, and Nexus certificates with expiry on 2026-10-24. `step-ca` health was healthy and the root fingerprint was unchanged.
- The Paperclip agent task itself was not run. The Hermes HTTPS path is ready for Sergey to test in Paperclip.

## Rollback and cleanup

- Pre-reissue certificate/key archive: `/mnt/bulk/debian-migration/step-ca/npm-homelab-https-pre-reissue-20261023-160310.tar.gz` (root-owned, mode 0600; private material).
- Pre-change step-ca Compose file: `/srv/containers/compose/step-ca/compose.yaml.pre-http01-dns-20261023-1612` (root-owned, mode 0600).
- Pre-change renewal script: `/srv/containers/compose/step-ca/renew-nginx-homelab.sh.pre-ca-dns-20261023-155434` (root-owned, mode 0600).
- To roll back the Compose change, restore the saved Compose file and recreate only `step-ca`; verify the root fingerprint and health. To restore the old certificate set, use the restricted archive and then test/reload NPM. The old certificates are expired, so this is emergency recovery only, not a usable steady state.
- Temporary issuance staging containing private keys and transfer/probe files was removed. No NPM routes, DNS policies, Paperclip agent settings, ACLs, or CA keys were changed.
