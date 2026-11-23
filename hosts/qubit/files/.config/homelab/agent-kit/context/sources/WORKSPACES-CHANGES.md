# Tensor OpenRGB window and workspace controls — 2026-10-14

## OpenRGB

- Added a permanent `openrgb-floating` Hyprland rule: floating, centered, requested 900×650.
- Applied it to the live compositor without reloading the entire monitor configuration.
- Resized/centered the existing client window. Actual size is 989×650 because OpenRGB enforces
  a minimum width. Floating true, fullscreen false.
- The OpenRGB SDK/server and RGB persistence services remain active; they were not restarted.
- Existing Super+drag/Super+V controls also apply to this window.

## Center workspace bar

- Corrected drag data transfer: a custom MIME target now receives raw UTF-8 bytes via
  Gtk.SelectionData.set, and the receiver decodes the raw data. The old set_text/get_text
  conversion did not match the custom MIME target.
- Added drag-source opacity and insertion-edge highlighting.
- Suspended bar rebuilding during dragging and finished the drag transfer before recreating widgets.
- Right or middle click now removes the workspace directly; the confirmation popover was removed.
- Removal moves applications to another occupied workspace (same monitor preferred), never closes/kills them.
- A last populated desktop is replaced with another destination while preserving its windows.
- Empty entries disappear automatically, including the previous synthetic/persistent workspace-10 handle.
- If the last app closes on the active primary desktop, the bar switches to another occupied primary
  desktop when available. A compositor still needs an active desktop per monitor; an empty internal
  desktop may remain while its bar entry is hidden.
- A new blank workspace created with plus remains visible while selected, until an app opens or the
  user leaves it. This permits creating a workspace and then launching applications into it.
- Saved order is pruned as entries disappear. Drag order is visual; existing numeric workspace IDs
  and keyboard workspace bindings are retained.
- The 120 ms plus fade and prior hover/workspace transitions remain in place.

## Operational checks

- workspace-strip.service, openrgb.service and tensor-rgb-persistence.service active.
- No current Hyprland configuration errors.
- Existing OpenRGB client verified floating at 989×650, not full screen.
- User mouse interaction confirmation requested; drag/drop and removal need that observation.

## Files and rollback

Changed: `~/.config/hypr/hyprland.lua`, `~/.config/waybar/workspace-strip.py`, `~/.config/waybar/style.css`.
Private Tensor backups: `~/.local/state/workspaces-fix-20261014/*.before`, including saved order when present.

Restore scripts/styles and saved order, reload Hyprland in its live session (or restore its rule on
next login), reload Waybar, then restart workspace-strip.service after the Waybar reload completes.
This removes the added permanent OpenRGB rule. The live OpenRGB rule can also be removed by a
compositor config reload after restoring hyprland.lua; there is no need to restart the RGB server.

Original and installed files are saved under this record's `current/` and `changed/` directories.

GTK transfer references:
[set](https://docs.gtk.org/gtk3/method.SelectionData.set.html),
[set_text](https://docs.gtk.org/gtk3/method.SelectionData.set_text.html),
[get_data](https://docs.gtk.org/gtk3/method.SelectionData.get_data.html).
