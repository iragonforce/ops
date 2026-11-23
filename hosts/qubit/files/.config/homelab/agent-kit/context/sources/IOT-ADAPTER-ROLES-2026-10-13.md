# Nexus IoT adapter roles — 2026-10-13

This supersedes the earlier ZBT-1 passthrough repair in
`HOME-ASSISTANT-USB-2026-10-13.md`. The user chose the existing Sonoff/Nordic
assignments, with the ZBT-1 retained as a spare.

## Active roles

| Hardware/service | Role | Verified state |
|---|---|---|
| Sonoff Dongle Plus V2 / Zigbee2MQTT | Zigbee coordinator; Home Assistant discovery through MQTT | Healthy; discovery enabled |
| Nordic Thread Co-Processor / OTBR | Thread radio and border router | Interface up; Thread leader |
| Home Assistant / Matter Server | Matter controller for Wi-Fi, Ethernet and Thread devices | Matter integration loaded; server running |
| Connect ZBT-1 | Spare; no active container mapping | Unmapped; firmware unchanged |

The MQTT, Thread, OTBR and Matter integrations all returned `loaded` through
Home Assistant's authenticated API. There is no ZHA integration configured.
No paired-device operation or new device commissioning was performed.

## Changes

- Removed the ZBT-1 mapping and its recently added `/run/udev` bind from
  Home Assistant's Compose service.
- Persisted the same settings in restoration overrides.
- Recreated only Home Assistant under the existing `nexus-iot` Compose project.
- Kept the Sonoff and Nordic stable USB identities and all service IP/MAC
  assignments, application data and firmware intact.
- All five relevant containers retain `restart: unless-stopped`.
- Home Assistant is healthy and its private Tailscale HTTPS endpoint returns
  HTTP 200 with valid TLS; no fresh adapter errors appeared after restart.

Do not rerun the historical `fix-ha-zbt1.py` installer unless the user explicitly
requests a new role for the spare adapter. Do not assign one radio to two services.

## Pairing

- Zigbee: enable permit-join in Zigbee2MQTT briefly, then put the device into
  pairing mode. Home Assistant receives device discovery over MQTT.
- Matter: use Home Assistant's Add Matter device workflow. For initial
  commissioning, the phone must be on the appropriate local IoT network;
  remote control over Tailscale is separate from local discovery/commissioning.

## Rollback

The private pre-change backup is `/var/lib/nexus-iot-roles/20261013-193932`.
Its `rollback.sh` restores the prior Compose file and overrides, then recreates
only Home Assistant. That restores ZBT-1 passthrough; it does not change firmware.
After later configuration changes, merge only these USB settings instead of
restoring entire older configuration files.
