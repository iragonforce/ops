# Private-file index — paths only

This file contains no credential values. Existing files should remain private and must not be bulk-ingested into prompts or reports. Retrieve only the credential needed for a current authorized operation, through the appropriate host/container path.

## Qubit

- `~/.config/homelab/unifi-api-key`: UniFi API credential.
- `~/.config/homelab/unifi-ssh-pswd`: UDR7 SSH credential.
- `~/.config/homelab/home-assistant-api-key`: HA administrator API token.
- `~/.config/homelab/a1-mini-lan-code`: updated Bambu local code supplied by user.
- `~/.config/homelab/petlibro.json`: private account configuration, API region US.
- `~/.config/homelab/checkmk-login.json`: Checkmk login reference.
- `/Users/iragonforce/encryption-key-bulk-fast.md`: user-provided original migration key reference. Do not copy it into this workspace.

## Nexus host

- `/etc/nexus/secrets/<stack>`: service credentials/environment files.
- `/etc/zfs/keys/bulk.key`: active bulk unlock key.
- `/etc/homelab/secrets/telegram-boot.json`: private boot-notification credential source.
- `/srv/containers/data/hermes/data/{auth.json,.env,config.yaml}`: Hermes provider/config material. Some configuration fields are secret; print only selected non-secret metadata if needed.
- `/etc/nexus/secrets/home-assistant/bambu-lan-code`: printer code reference from recorded integration work.
- Home Assistant `.storage`, Thread datasets and private rollback directories can contain secrets and pairing state. They are not generic context documents.

The original conversation included passwords and a Wi-Fi password. None are reproduced here. Do not recover them from chat merely to populate memory. Prefer existing private files and interactive login.
