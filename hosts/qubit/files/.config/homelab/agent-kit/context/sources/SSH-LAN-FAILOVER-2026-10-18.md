# LAN-first SSH failover, 2026-10-18

## Current behavior

On Qubit, Tensor and Nexus, `ssh qubit`, `ssh tensor` and `ssh nexus` use the same rule. A small OpenSSH ProxyCommand tries the target's management LAN IP with a five-second TCP connect timeout. If that fails, it tries the target's Tailscale IP with the same timeout. If both fail, it reports both connection errors. Successful TCP connection is handed to normal OpenSSH. Host-key or authentication failure remains an error, rather than silently trying another path. Tmux's existing SSH detach and return wrapper still invokes ordinary SSH and therefore uses this rule.

Route-specific `qubit-ts`, `tensor-ts`, `nexus-ts`, `*-lan`, and `*-local` host aliases were removed from active user SSH config on the three machines. Recovery-only `*-bootstrap` names, numeric-address node automation entries on Nexus, and unrelated SSH hosts were preserved. The older source `CLIPBOARD-SSH-2026-10-18.md` records the preceding Qubit Tailscale-only setting; this source supersedes that routing detail.

The maintained proxy source is `tools/homelab-ssh-connect`, installed at `~/.local/bin/homelab-ssh-connect` by `admin/install-host.py`. Each host's private `~/.ssh/homelab-routing.conf` is included first from `~/.ssh/config`; it holds that host's existing keys and host-key aliases. The proxy source contains only public endpoint addresses, no credentials.

## Operational checks

- Candidate routing files connected from each source host to each of the three targets as `iragonforce` before deployment.
- After deployment, `ssh -G` on all nine source/target pairs showed the LAN HostName, strict host-key checking and the proxy command. All nine ordinary batch SSH connections returned `iragonforce`.
- Active SSH config searches found no route-specific `-lan`, `-ts` or `-local` host aliases. The existing Qubit/Tensor/Nexus host-key aliases were retained.
- A verbose Qubit-to-Nexus SSH connection observed LAN port 22 time out, then Tailscale port 22 connect and authenticate as `iragonforce`. No outage was induced; other source/target fallback cases were not forced.

The historical `truenas`/`arch` root aliases and their `-lan` variants were also removed from Qubit and Tensor as part of reducing old route names. Their old config is in the rollback copies.

## Rollback

Prechange Qubit SSH config, config.d, routing file and proxy are in `/Users/iragonforce/.local/state/ssh-routing-20261018/`. Tensor and Nexus each hold their prechange SSH config and config.d at `~/.local/state/ssh-routing-20261018/`. Nexus's old self-route include was moved intact to `~/.local/state/ssh-routing-20261018/00-nexus-self.disabled`. Restore only the needed files and preserve later edits; the kit's maintained proxy/installer can be reverted separately if restoring the previous alias scheme.
