# Hermes SSH access — 2026-10-15, America/Toronto

## Before

Nexus's ordinary iragonforce account could connect to Qubit and Tensor with existing aliases and keys. Verified hostname and username from both remote machines. Hermes's actual named container user (UID 10000) had an SSH client but no `.ssh` directory, key or aliases. Bare names did not resolve, and TCP22 from the container to management addresses timed out.

## Configured

- Dedicated Ed25519 key generated inside the persistent Hermes home: `/opt/data/.ssh/id_ed25519_homelab`. Its private contents were not exported or logged. Owner hermes; directory 0700 and private files 0600.
- Authorized that public key for iragonforce on Qubit and Tensor. Restricted its source to 192.168.5.55, disabled agent and X11 forwarding, preserved existing authorized keys.
- Added strict host-key verification using ED25519 host public keys read over existing trusted paths: Qubit's local host-key file and Tensor's already-trusted SSH connection. No blind host-key acceptance or verification bypass.
- Persistent aliases: `qubit` / `qubit-wired` / matching homelab.lan names → 192.168.1.4; `qubit-wifi` → 192.168.1.102; `tensor` / tensor.homelab.lan → 192.168.1.3. Login user iragonforce. The plain qubit alias uses wired Ethernet; use qubit-wifi when Ethernet is disconnected.
- Added one exact UniFi rule permitting source 192.168.5.55 to destinations 192.168.1.4, 192.168.1.102 and 192.168.1.3 on TCP22. Rule ID `7962bda8-ae24-4ddf-b3ef-8152c85480b7`; name `Nexus: Hermes SSH to Qubit and Tensor`. UniFi creates a derived return rule. The exception precedes existing Applications→Internal denials; unrelated rules are retained.

No container recreation, host reboot or desktop restart was needed. All profiles share the same OS-level SSH configuration and dedicated identity in the central Nexus container.

## Operational checks

- Nexus host → Qubit and Tensor: hostname and iragonforce returned successfully before changes.
- Actual Hermes named container user → Qubit and Tensor: successful passwordless, strict-key SSH after changes.
- Actual Hermes `tools.terminal_tool.terminal_tool` → both machines, separately under nexus/tensor/qubit profile configuration: every command returned exit_code 0 and the expected hostname and username.
- Checks ran harmless hostname/id commands. No model inference or formal test suite was used. No off-site/Tailscale SSH routing is claimed; these connections use the LAN.
- A vendor Python SyntaxWarning appeared while importing the terminal backend; it did not prevent successful tool execution. No vendor source modification was made.

## Use inside Hermes

```sh
ssh qubit 'hostname'
ssh tensor 'hostname'
ssh qubit-wifi 'hostname'  # alternate interface when appropriate
```

These commands execute as iragonforce on the destination. The source terminal remains Nexus Docker. Host OS permissions and existing sudo policies apply.

## Recovery and rollback

Private container SSH before-state: `/opt/data/recovery/ssh-20261015-114937`, host `/srv/containers/data/hermes/data/recovery/ssh-20261015-114937`. No prior `.ssh` directory existed during this setup. On each destination, original authorized_keys is backed up at `~/.local/state/hermes-ssh/20261015-114937/authorized_keys`.

To revoke access, remove only the public-key entry commented `hermes-nexus-homelab` from each destination's authorized_keys and remove the exact UniFi SSH policy and its derived return rule. Then remove the managed block in Hermes `.ssh/config` and the dedicated key/known-host entries if no longer needed. Compare against intervening changes before restoring whole files.

Original firewall ordering and rollback metadata: Qubit task directory `outputs/agent-kit-work/private/ssh-20261015-114937`. Do not replay an old entire ordering after unrelated router edits. Existing human/operator SSH keys and aliases were not replaced.
