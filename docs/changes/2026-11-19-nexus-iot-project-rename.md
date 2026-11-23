# Nexus IoT Docker project rename

Date: 2026-11-19 21:15 EST

## Objective

Rename Docker Compose project `nexus-iot` to `iot` without
changing container names, images, IP addresses, persistent
storage, device mappings or external networks.

## Verified outcome

- Six containers recreated and running under project `iot`.
- All applicable Docker healthchecks passed.
- Existing IPv4 assignments, image references, bind mounts
  and USB device mappings verified unchanged.
- Compose configuration identical between projects except
  for the project name.
- Updated Glance network mapping and service identifier.
- No inventory entry referenced the old project name.

## Backups

Cold application data:
`/var/backups/homelab/docker-stage6j-iot-SeBwurf1`

Glance configuration:
`/var/backups/homelab/docker-stage6j-git-2uwqjo2h`

## Rollback

Restore the previous Glance files from Git or the backup above.
If the Docker project itself must be reverted, inspect current
runtime state and take a fresh data backup first, then use the
original Compose file with `-p nexus-iot`. Do not run both
projects simultaneously or overwrite newer application data.

## Limitations

Application-level Matter, Thread and Zigbee communication
was not independently tested beyond container startup,
healthchecks and preservation of device/network configuration.
