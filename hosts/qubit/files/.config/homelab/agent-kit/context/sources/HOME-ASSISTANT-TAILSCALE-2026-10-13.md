# Home Assistant private Tailscale HTTPS — 2026-10-13

## iPhone connection

**URL: `https://nexus.tail4e4f0f.ts.net:8443`**

With Tailscale connected on the iPhone, open Home Assistant Companion, enter this address manually, and sign in with the existing Home Assistant account. An existing app server can use this as its external URL. This endpoint also works while at home with Tailscale enabled.

The iPhone is `signal.tail4e4f0f.ts.net`, IPv4 `100.109.161.19`, IPv6 `fd7a:115c:a1e0::b439:a113`. Tailscale reported it online. Its addresses are covered by the existing tailnet access policy for port 8443. No additional router, SSH, SMB or NFS access was granted to the phone.

## Implemented path

`iPhone → Tailscale HTTPS :8443 → 127.0.0.1:18123 → Home Assistant 172.16.11.19:30103`

- Tailscale Serve terminates HTTPS and forwards HTTP/WebSocket traffic with the original client address headers.
- The loopback relay binds only `127.0.0.1:18123` and runs through `nexus-ha-tailscale-relay.service` using a dynamic unprivileged user.
- Home Assistant's pinned private bridge IP is unchanged. Its existing trusted-proxy range `172.16.11.0/24` includes the relay source `172.16.11.1`, so Home Assistant settings and authentication did not require modification.
- Tailscale Serve runs in persistent background mode. The relay and tailscaled are enabled at boot.
- Port 443 continues serving the existing NPM routes. No public Funnel was enabled.
- Existing tailnet access policies apply; this is not a phone-only ACL. Home Assistant login remains required.

## Verification

- HTTPS returned HTTP 200 from Qubit over Tailscale, with certificate verification successful.
- The Home Assistant WebSocket endpoint returned HTTP 101 and its expected `auth_required` message.
- An HTTP request carrying the phone's forwarded address was accepted by Home Assistant.
- Relay binding was confirmed loopback-only; both startup services are enabled.
- The phone's connection is permitted by the current IPv4/IPv6 tailnet rules. An actual iPhone app login still requires the user to enter the URL and credentials.

## Records and rollback

Private records: `/var/lib/nexus-ha-tailscale-20261013/serve-before.json` and `serve-after.json`. The relay unit is `/etc/systemd/system/nexus-ha-tailscale-relay.service`.

To remove this endpoint only:

```sh
sudo tailscale serve --https=8443 off
sudo systemctl disable --now nexus-ha-tailscale-relay.service
```

No Home Assistant configuration or container rebuild is needed for rollback. Restore the saved relay unit if it existed before this change. Do not reset other Tailscale Serve endpoints.
