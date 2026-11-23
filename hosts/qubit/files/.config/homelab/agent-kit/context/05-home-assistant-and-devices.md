# Home Assistant and physical devices

## Radios and protocols — latest recorded roles

| Component | Assignment |
|---|---|
| Sonoff Dongle Plus V2 | Zigbee coordinator owned by Zigbee2MQTT; HA discovery through MQTT |
| Nordic Thread co-processor | OTBR's Thread radio/border router |
| Home Assistant + Matter Server | Matter controller for supported Wi-Fi/Ethernet/Thread devices |
| Connect ZBT-1 | Spare, no active passthrough, firmware unchanged |

The 2026-10-13 radio-role record supersedes the earlier temporary ZBT-1 mapping into HA. Do not rerun the old ZBT-1 fixer or flash SPINEL/Thread firmware to Zigbee without a new user decision. Stable `/dev/serial/by-id` identities and single-process radio ownership matter.

The earlier API checks showed MQTT, Matter, OTBR and Thread loaded, but did not commission devices. **The live handoff inventory shows `otbr` exited while Home Assistant remains healthy.** Reconcile that state with current user intent and inspect private logs without exposing Thread credentials before changing anything.

Home Assistant's private tailnet HTTPS is `https://nexus.tail4e4f0f.ts.net:8443`. An iPhone using Tailscale can control HA remotely. Initial Matter/Thread discovery and commissioning may require local network/multicast connectivity; remote access alone is not equivalent.

## Devices

- Wemo WSP080 plugs and Eve Energy Strip: user confirmed direct Apple Home pairing. Do not reset them or assume they were subsequently paired into HA.
- Bambu **A1 Mini**, not A1: reserved `192.168.4.229`, LAN Only and Developer Mode enabled by user. Community `greghesp/ha-bambulab` 2.2.26 was installed; local MQTT telemetry and a JPEG camera response were checked. The old access code failed; the corrected code is private. Pause/resume/stop were attempted while idle and cannot be treated as an active-print control verification. The dated note also observed a hotend/nozzle HMS fault; recheck current physical status before print-related commands.
- HP OfficeJet 3830: existing IPP integration at `192.168.4.111`, with recorded ink/status telemetry. Existing pairing was preserved.
- PETLIBRO PLAF301: community integration `jjjonesjr33/petlibro` v1.2.32 was configured and loaded. API region is `US`, separate from Toronto device timezone. Some entities are unsupported/unknown. No feeding or schedule changes were exercised. Not exported to HomeKit. Reusing the phone-app account may affect its session; see source note.

## HomeKit and telemetry

The existing `Tensor Home` bridge and pairing identities were preserved. Printer binary indicators, momentary control switches and a cooling-fan entity were added according to the printer record; physical Apple Home behavior was not confirmed. Do not replace `.storage` or HomeKit allocation/pairing files with an old full backup.

Tensor RGB/visual standby/power controls were integrated earlier. Hardware component telemetry and Docker status reach HA over MQTT and appear in Grafana/HA dashboards. CPU/GPU energy is partial component consumption, not whole-machine wall power; the machines have no energy-monitoring plugs. Do not label container CPU percentage as measured container watts or promise arbitrary sensor display in Apple Home.

Use current authenticated HA APIs/config flows and targeted YAML changes. Preserve radio network datasets, entity IDs, automations, bridge IDs and existing credentials. Private token/code paths are indexed separately; their contents do not belong in prompts.
