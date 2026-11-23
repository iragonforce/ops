# Visual standby

`hibernate` turns both displays off, loads OpenRGB's saved `Off` profile, and switches each OpenLinkHub controller to its saved `Off` profile. The computer remains awake.

Press Ctrl+L to wake it. This runs `hibernate resume`, which turns the displays on, loads OpenRGB's saved `Default` profile, and switches each OpenLinkHub controller to its saved `default` profile. `hibernate resume` can also be run manually, including over SSH. `hibernate status` prints `awake` or `visual standby`.

The command does not save or restore the previous lighting state. It uses the existing profiles in `~/.config/OpenRGB/profiles/` and OpenLinkHub. A runtime marker at `/run/user/1000/tensor-visual-standby.json` tells the Ctrl+L shortcut when to resume. The regular Hypridle timeout also calls `hibernate`.
