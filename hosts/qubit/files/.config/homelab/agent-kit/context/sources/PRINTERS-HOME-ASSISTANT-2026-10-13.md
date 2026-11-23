# Printer integrations — 2026-10-13

## HP OfficeJet 3830

Existing IPP integration retained at `192.168.4.111`.
Authenticated Home Assistant checks reported printer state `idle`, black ink
100%, and tri-color ink 50%. No HP settings were changed.

## Bambu Lab A1 Mini

Reserved address: `192.168.4.229`.

Installed the community `greghesp/ha-bambulab` integration, stable version
2.2.26, directly under `custom_components/bambu_lab`. HACS is not installed.
Home Assistant was restarted to load it.

Release:
`https://github.com/greghesp/ha-bambulab/releases/tag/v2.2.26`

Release asset SHA-256:
`fc72606c55f76e5d0401b98723fe67a637faf01cdc16494572bcc228ca83cdcd`

The downloaded asset matched the digest supplied by GitHub's release API.
The archive paths and manifest were checked before extraction.

The old MCP access code was rejected. The user subsequently supplied an updated
code in a private file and confirmed LAN Only Mode and Developer Mode are on.
Home Assistant now connects over local MQTT. The printer identifies itself as
**A1MINI**, correcting the previous A1 label. Its entry and device are named
`Bambu A1 Mini`.

The Bambu integration is loaded; local telemetry is available. The Developer LAN
Mode entity reports on and the control-blocked entity reports off. An authenticated
camera request returned HTTP 200 with a valid JPEG image. Firmware updates remain
disabled. The existing MCP credential was not modified.

No printer firmware, cloud account, print job, heater, fan, pause, resume or stop
action was changed or executed by this setup. The LAN/Developer settings were
enabled by the user. The local code is stored privately under
`/etc/nexus/secrets/home-assistant/bambu-lan-code` and in Home Assistant's private
integration settings; it is excluded from this report and chat.

## Apple Home

Extended the existing `Tensor Home` bridge, retaining its name, address, port
21065, original four Tensor entities, accessory IDs and all three paired clients.
Added eight accessories:

- A1 Mini Printing, Finished and Problem: template binary indicators.
- A1 Mini Online: existing printer connectivity indicator.
- A1 Mini Pause, Resume and Stop: existing momentary button entities, represented
  as switches in Apple Home.
- A1 Mini Cooling Fan: existing fan entity.

The bridge is configured through `packages/tensor_control.yaml`, so its filter
was updated in YAML and reloaded through the supported HomeKit reload service.
No new bridge or pairing was created. All twelve expected accessories are
allocated and the bridge's authenticated HAP endpoint is listening. An
unauthenticated request returns HTTP 401 as expected.

Native printer status, progress percentages and ink percentages have no dedicated
Apple Home printer accessory type. Binary indicators appear as sensor accessories.
The camera remains available in Home Assistant and was not added to Apple Home.
Heater controls and other printer buttons were not exported.

Pause/resume/stop were unavailable in the current failed/idle state. Their
physical operation and display on the user's Apple Home clients remain unverified;
no active print was started to exercise them.

## Printer-reported fault

The printer reports HMS `0300_0200_0001_0009`, severity `fatal`: nozzle temperature
control is abnormal and the hotend may not be installed. Current print state is
`failed`; Printing and Finished indicators are off and Problem is on. This fault
was observed in printer telemetry and was not caused by a command from this setup.
Check the physical hotend before printing. Manufacturer troubleshooting:
`https://wiki.bambulab.com/en/a1-mini/troubleshooting/hmscode/0300_0200_0001_0009`.

## Recovery and maintenance

Private backup: `/var/lib/nexus-bambu-ha-20261013` (mode 0700).
It contains pre-install `.storage`, configuration.yaml, the release asset,
release metadata and non-secret setup summaries. It also contains the pre-HomeKit
storage backup, original HomeKit options and original Tensor package YAML.

HomeKit rollback: restore only the original include filter from
`homekit-options-before.json` to the Tensor package, preserving newer unrelated
settings; invoke HomeKit reload. Remove the three added template helper entries
through the supported Home Assistant API/UI after removing them from the bridge.
Do not overwrite HomeKit pairing state or accessory allocation files.

To remove this integration: remove its config entry through Home Assistant if
one has been created, stop Home Assistant, move `custom_components/bambu_lab`
into the private backup, and restart Home Assistant. Restore only affected
configuration files if required; avoid overwriting newer auth sessions or
unrelated device settings with the full older `.storage` backup.

Future upgrades must use explicit stable releases and matched recovery copies.
