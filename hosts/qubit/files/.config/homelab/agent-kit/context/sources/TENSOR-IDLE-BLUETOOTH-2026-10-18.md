# Tensor ten-minute visual standby and Bluetooth reconnect

2026-10-18, America/Toronto.

## Requested behavior and current state

The user requested visual standby after ten minutes of inactivity and asked about faster Keychron K2 V2 Bluetooth reconnection.

Hypridle was already configured with timeout 600 and on-timeout ~/.local/bin/hibernate. Confirmed those values and restarted only the user hypridle service to reload the current configuration. Existing explicit wake shortcuts, inhibit handling and the new OpenLinkHub/OpenRGB lighting policy were preserved. Host processes and SSH remain awake. No actual ten-minute wait or monitor blanking was performed for this check.

The K2 uses the Classic Bluetooth HID profile. The controller supports FastConnectable, but it was disabled. Saved /etc/bluetooth/main.conf and the prior runtime setting, enabled FastConnectable live with btmgmt fast-conn on, and persisted FastConnectable = true in the General section of main.conf. Bluetooth was not restarted; no pairing/trust stores, visibility policy, firmware or device-specific keys were changed. No continuous discovery loop, custom polling service or recurring job was added.

## Checks and practical limits

- Hypridle active, configured timeout 600, hibernate action present.
- FastConnectable enabled in live controller readback and persistent configuration; Bluetooth service active.
- The option can reduce incoming connection delay at a power cost. It cannot force a sleeping keyboard to wake. Reconnection latency still needs physical user comparison.
- Keychron documents Fn+S+O held for three seconds as the K2 auto-sleep toggle. Disabling keyboard sleep can reduce keyboard-side delay and increases battery use. This is a physical keyboard action; it was not performed remotely.

Sources: https://github.com/bluez/bluez/blob/master/src/main.conf and https://www.keychron.com/blogs/news/k2-key-combinations .

## Rollback

Tensor /var/backups/homelab/bluetooth-fast-connect-20261018 contains main.conf.before, runtime-before.json and ROLLBACK.md. Restore the saved configuration; if reverting the former disabled runtime state, use sudo btmgmt fast-conn off. No daemon restart is needed for that live rollback. The idle file was already at the requested value and was not edited.
