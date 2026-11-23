# Tensor: desktop, standby, SSH and mouse

2026-10-18 idle/Bluetooth: verified and reloaded the existing 600-second hypridle → `hibernate` configuration. Enabled supported BlueZ FastConnectable live and in `/etc/bluetooth/main.conf`, without restarting Bluetooth or changing device identity records. Faster physical reconnection remains unmeasured; K2 auto-sleep is a separate keyboard-side factor. Source/rollback: [TENSOR-IDLE-BLUETOOTH-2026-10-18.md](sources/TENSOR-IDLE-BLUETOOTH-2026-10-18.md).

2026-10-18 lighting policy: `hibernate` now selects native OpenLinkHub **Off** without enabling its OpenRGB integration; wake loads OpenRGB **Default** for native controllers and restores the original native hub awake profiles. Preserved case/AIO lighting, curve assignments and the existing Off safety ramp. Repaired Default's stale detector identities/LED counts and restarted the existing RGB/checkpoint services. A lighting-only Off/wake cycle passed; full monitor/keyboard wake and portrait flicker were not exercised. Source and rollback: [TENSOR-STANDBY-LIGHTING-2026-10-18.md](sources/TENSOR-STANDBY-LIGHTING-2026-10-18.md).

2026-10-18 Minecraft launcher: `~/.local/bin/minecraft` runs `mcpelauncher-ui-qt`. It now reads the active Wayland session from `systemctl --user show-environment`, validates the display socket, then starts the launcher; this permits launching from SSH or stale tmux panes. The prior signal 6 was a Qt Wayland display failure. A plain-SSH launch produced a running process and Hyprland window; graphical interaction remains unchecked. Rollback: `~/.local/state/minecraft-launcher-20261018/minecraft.before`.

2026-10-16 Wallpaper Engine picker: Tensor `~/.local/bin/wallpaper-engine-browser` blocked on a synchronous Steam client subprocess and never executed `wallpaper64.exe -showbrowse`. The helper now uses asynchronous Steam startup only when Wallpaper Engine is absent. Operational readback after starting it: `Wallpaper UI` mapped on workspace 5 at 3440×1440; physical appearance still needs confirmation. Rollback and log: kit CHANGELOG.md; Tensor `~/.local/state/wallpaper-browser-20261016/`. The separate DP-3 Linux renderer had a process but no layer surface; investigate separately if the portrait wallpaper remains missing.

2026-10-16 utility window rules: Tensor `~/.config/hypr/hyprland.lua` now floats and unpins the titled Wallpaper UI picker, Blueman Manager and Solaar; removes compositor decorations/shadows/borders and centers/sizes them on opening. Existing windows were floated/resized without killing apps. Live Hyprland configerrors empty and all three clients floating/pinned=false. Fresh launch and physical dragging/decorations still need user confirmation. Rollback and dated check: kit CHANGELOG.md; Tensor `~/.local/state/utility-window-rules-20261016/hyprland.lua.before`.

## Hardware and current software records

- RTX 5070 drives the main LG ultrawide on DP-5, 3440×1440 at approximately 160 Hz.
- AMD integrated Radeon drives the portrait LG 4K display on DP-3, 3840×2160, transform 3, scale 1.666667, 60 Hz, 8-bit SDR, VRR off.
- Recorded versions at the latest reboot: kernel 7.2.9-arch1-1, Hyprland 0.56.2, Aquamarine 0.15.1, NVIDIA 615.78.08.

## Visual standby

2026-10-16 user correction: Tensor tmux layout reconciliation must never move an occupied slot aside or create a replacement. Removed that branch entirely; unrecognized occupied slots are skipped unchanged. Missing slots can still initialize. Verified two further reconciliations preserve all pane/window/PIDs. Existing previous-zsh 10/11 remain open pending explicit closure.

`hibernate` invokes the custom visual standby helper, not system hibernation. `hibernate resume` wakes monitors and restores the saved lighting state; fans return to the default OpenLinkHub profile. As of 2026-10-16, Hypridle enters after 600 seconds with no input-resume listeners. Ctrl+L or Super+L resumes visual standby; Ctrl+L passes through while awake, and Super+L still password-locks while awake. Both work in the Dota submap. Ordinary key/mouse DPMS wake is explicitly disabled. SSH and processes stay running; automatic standby does not itself password-lock or block blind input. Live configuration/bindings/daemon checked; physical ten-minute inactivity and shortcut-only wake remain unverified. Rollback: Tensor `~/.local/state/idle-tmux-20261016-1425/`. Existing administrative resume commands remain recovery paths.

Tensor tmux 2026-10-16: installed/local-kit layout helper now preserves role-tagged or recognized managed windows regardless of transient foreground programs and no longer migrates live Hermes panes for launcher revision/name changes. Two reconciliations preserved every pane/window/PID and added no windows. Existing `10:previous-zsh` and `11:previous-zsh` were preserved. Their move-aside mechanism is confirmed in the old helper; exact past triggering commands were not logged. Qubit canonical source was not updated; preserve Tensor's override during kit sync.

Real suspend/hibernation are disabled by systemd sleep policy; logind ignores relevant idle/sleep actions. This is deliberate. Do not enable true sleep to fix a cosmetic issue.

Scripts: `~/.local/share/tensor-control/{visual-standby.py,tensor-desktop.py,tensor-rgb.py}`. Commands under `~/.local/bin`. RGB snapshots preserve native modes/colors and OpenLinkHub state. Boot-state persistence avoids saving the forced standby-off appearance as the preferred boot state.

OpenLinkHub's existing `Off` fan curve stops non-AIO fans but ramps them rapidly at 75°C. AIO/pump cooling and that thermal safety must be retained. The user confirmed RGB was off across the PC after earlier repairs.

## 2026-10-26 — Main-display window placement

Both displays remain active; DP-3 is reserved for workspace 10/btop, while normal new windows are directed to DP-5. Rofi now uses a user wrapper with `-m DP-5`. Modal child windows float, and a Hyprland-native Zen extension-window hook floats and centers extension top-level windows. Middle-button click cycles tile/float/fullscreen and middle-button drag moves windows; native edge snapping is enabled. Live reload/config readback passed; physical interaction and browser popup behavior remain pending. Backup and rollback: Tensor `~/.local/state/hypr-window-placement-20261026/`; see kit CHANGELOG. An active monitor necessarily remains in the compositor's coordinate space even when ordinary windows are kept off it.
The user confirmed there is currently no visual problem on the 4K panel, saved work, and authorized a fresh Hyprland session. The compositor exited cleanly and autologin relaunched it. Both monitors and normal startup apps returned with no config errors; XP-Pen mapping persisted. Physical new-binding and popup behavior still awaits user use.

## Flicker — unresolved

The portrait 4K display repeatedly flashes green on content updates after wake. A manual 30→60 Hz mode reset temporarily cleared it, but recurrence was user-confirmed. Earlier no-flicker confirmations after one cycle are not proof of a permanent fix.

Latest 2026-10-14 changes:

1. Desktop helpers discover the compositor directly and use bounded subprocess calls; a stalled user manager no longer blocks display recovery indefinitely.
2. Repeated automatic 30/60 Hz mode resets were removed after the user reported blinking. `monitors repair` remains an explicit manual action.
3. `AQ_MGPU_NO_EXPLICIT=1` was added early in `~/.config/hypr/hyprland.lua` as a cross-GPU synchronization workaround. Aquamarine caches the old value in an existing session. A fresh Hyprland session is still required.
4. A desktop restart was proposed but the user switched to mouse setup. No authorized restart or physical validation of the new backend setting is recorded. Do not close GUI apps with unsaved work without coordinating with the user.

Backups and exact rollback: `sources/TENSOR-STANDBY-CHANGES.md`, `sources/TENSOR-STANDBY-ROLLBACK.md`; remote user backups under `~/.local/state/standby-stability-20261014/before/`.

## SSH and network outages

There were at least two different failure paths. An earlier Intel I226-V link detachment was mitigated with per-device ASPM/runtime power settings and EEE already off. A later outage occurred while systemd's generator sandbox reload stalled; SSH debug logs stopped in local user/group lookup. Do not conflate them.

The latest targeted sshd changes bypass userdb IPC, use local authorized keys, disable reverse DNS and reduce DEBUG3 logging to INFO. Global NSS/PAM were not rewritten. This does not establish the underlying systemd generator failure's cause or guarantee access if PID1 freezes again.

Separately, the `ssh tensor` alias hit Tailscale SSH's browser reauthorization wait. Tailscale SSH interception was disabled on Tensor; normal key-based OpenSSH over Tailscale now works. Fresh alias/LAN/Tailscale connections succeeded in roughly 0.16–0.17 seconds. During a 10-second visual standby check, LAN SSH and HTTPS internet access worked; systemd reported running. No full-speed bandwidth test was performed.

## Desktop applications and Waybar

2026-10-15: repaired center strip's stale DPMS monitor selection. Its live process had cached `WAYBAR_PRIMARY_OUTPUT=FALLBACK` although Hyprland had DP-5/DP-3 again. Removed launcher caching, resolve live physical monitor per refresh, retain last good buttons during FALLBACK-only transitions, and retry refresh every two seconds with bounded IPC calls. Restarted only the center strip. Live journal renders IDs 10,1,2,3,5 on DP-5; one layer surface is 268px wide. Existing standby bar-recovery entry point was exercised successfully. Physical appearance/full standby cycles remain user checks. Rollback files are under Tensor `~/.local/state/workspace-strip-resume-fix/`; details in `sources/WORKSPACE-STRIP-RESUME-2026-10-15.md`.

- Obsidian launches through `~/.local/bin/obsidian-gpu`; RTX GPU compositing/WebGL/rasterization were checked. Preserve its startup wrapper and fullscreen behavior.
- XP-Pen and OpenRGB GUI use small floating windows. Keep the OpenRGB SDK server separate from GUI lifecycle.
- Left/right bars are Waybar; the center workspace strip is a custom GTK application under `~/.config/waybar/workspace-strip.py`.
- Center strip has hover-edge plus, drag ordering, close/move behavior and empty-workspace filtering. Drag/close physical confirmation remains pending. Closing a workspace must preserve its apps by moving them elsewhere.
- Workspace/hover transitions are approximately 50–180 ms, with a 120 ms plus fade. Source notes describe exact implementation.

## MX Master 3 — configured 2026-10-14

Unifying receiver, paired serial `883F2247`, Easy-Switch channel 2. Solaar 1.1.20-2 now starts with the graphical session. Device readback confirmed online, battery 100%, 1000 DPI, ratcheted/adaptive SmartShift threshold 20, and thumb-rest button diversion.

| Thumb-rest action | Mapping |
|---|---|
| Click | Application launcher |
| Hold + move left/right | Previous/next existing workspace |
| Hold + move up | Toggle fullscreen |
| Hold + move down | Toggle floating |

Rules live under `~/.config/solaar/rules.yaml`; actions call `~/.local/bin/mx-master-action` and native Hyprland APIs, avoiding synthetic modifier keys. Back/Forward, middle-click, wheel-mode button and horizontal wheel scrolling retain normal behavior. `mx-master-settings` opens Solaar. Physical gesture response awaits user confirmation.

Input Remapper 2.2.1-1 is installed but inactive; old presets and empty autoload configuration were preserved. Do not activate them indiscriminately. Keychron K2 V2 is present, but firmware history/Fn-key exposure and desired remaps remain unverified; no firmware was flashed by this work.

## Keychron Bluetooth investigation — 2026-10-16, recovered

Outcome: the user completed the dedicated local-agent flow and confirmed typing works. Helper status reported secure pairing and Linux Bluetooth keyboard registration; read-back input inventory showed Keychron K2 on bus 0005. Earlier failed attempts below are historical, not current unresolved state. No Bluetooth security weakening or firmware change was needed.

K2 transport/service discovery can succeed while BlueZ's classic HID security prerequisite fails and no Bluetooth input node appears. User confirmed correct long Fn+1 hold/rapid flashing. Re-pairing through the ordinary GUI has not resolved it; exact cause of missing persistent authentication remains unproven. A Blueman cancellation was observed for an earlier attempt, not proof every subsequent attempt was canceled. USB input is a separate path. keyd/input-remapper inactive. Service restarted once and adapter powered on again; later direct pairing/discovery failed, so the old connected state must not be assumed current. No firmware or security settings changed.

Launched a verified local GTK helper on Tensor workspace 5: ~/.cache/keychron-secure-setup-20261016.py, title Keychron K2 — secure Bluetooth setup. It uses its own per-client authentication agent, never becomes the default, and requires local confirmation before replacing only the K2 entry. Codes stay on-screen; status-only JSON is ~/.cache/keychron-secure-setup-status.json. At handoff it was waiting for local confirmation, not a completed repair. After user interaction, inspect status and Bluetooth input nodes, then request physical typing confirmation. Close/remove the helper and its status/error files for cleanup; any user-confirmed K2 pairing replacement requires pairing again to recover, not credential-file restoration.

## XP-Pen Deco 01 V3 — recognized 2026-10-16

Tablet is USB 28bd:0947, Deco 01 V3. Legacy driver xppenlinux-v3 3.4.9-240607 lacked model support although Linux enumerated physical inputs and device access worked. Replaced it with locally packaged official v4 driver xppenlinux-v4 4.0.15-260422.1 from https://www.xp-pen.com/download/deco-01-v3.html. Recipe/vendor archive/package and rollback files: Tensor ~/.local/state/xppen-driver-20261016/. Root installer was not run. Kept existing XWayland launcher/session-start route and device permissions; no global vendor autostart was added. Config directory remains vendor-required /usr/lib/pentablet/conf/xppen, writable only to root/primary group 1000, not world-writable. Portable v4 trials still read the hard-coded installed config, so binary-only staging is not a valid complete install.

Verified active /usr/lib/pentablet/PenTablet, successful v4 config load, UI model label Deco 01 V3, USB handle ownership, virtual pen devices, and visible floating settings window on workspace 5. Package file check: 107 files, none missing. Physical pressure/buttons/screen mapping remain unverified. One startup SentCmd(0,1,0) Failed warning has unknown effect despite successful recognition. No firmware or desktop reboot.

Rollback: stop only PenTablet; reinstall before/xppenlinux-v3-3.4.9-240607-x86_64.pkg.tar.zst with pacman -U, restore before/legacy-conf to /usr/lib/pentablet/conf, then use existing xppentablet-wayland launcher. Old image/config/launchers are preserved together. The temporary portable v4 staging directory is not used by startup.

Follow-up: user confirmed tablet works and requested ultrawide-only mapping. Selected Monitor2(1296,0,3440,1440) through the real XP-Pen Work area UI; OCR and saved XML read-back agree: DecoV2/Common/ScreenMapping id=2, SX=1296, SY=0, SW=3440, SH=1440. Keep that XWayland offset intact. Active Hyprland Lua maps only native ugtablet-deco-01-v3-pen to DP-5; vendor virtual pen/eraser/mouse use the app's work area and must not be mapped a second time. Config-only reload had no errors; monitors and normal mouse unchanged. Physical edge/mapping acceptance remains pending. Mapping-only rollback backups: Tensor ~/.local/state/xppen-ultrawide-20261016/{hyprland.lua,config.xml}. Reselect the driver output if display ordering/topology changes.

2026-10-26: the saved work area had reverted to the full 4736×2304 desktop. Stopped only the XP-Pen driver, restored its previously selected Monitor2/ultrawide mapping (id=2; 1296,0,3440,1440), and relaunched it. Added `~/.local/bin/xppentablet` as the interactive and Hyprland startup entry point, wrapping the existing `xppentablet-wayland`. Fresh SSH invocation with `--background` kept one driver process; XML readback after launch retained the main-display mapping. Backups: `~/.local/state/xppen-wrapper-20261026/`. Physical pen edge coverage was not yet checked at that point; the authorized subsequent fresh session started the driver once and retained the XML mapping.

2026-10-26 correction: the user found that the stylus still crossed onto the 4K output. The vendor virtual `xp-pen-pen` and `xp-pen-eraser` had no Hyprland output binding, while the native pen did. Bound all three tablet pen devices to DP-5 in the Lua config and reloaded Hyprland. The user physically confirmed confinement to the ultrawide and reach to all four edges. The earlier warning against mapping the virtual devices twice was disproved for this active driver/compositor combination. The virtual XP-Pen mouse is relative input and was not assigned a tablet output. Rollback: Tensor `~/.local/state/xppen-output-map-20261026/`; vendor XML retained.


## 2026-10-17 — Tensor poweroff investigation and SSH acceptance

Read-only inspection found poweroff reached final userspace shutdown at Oct 16 21:26:28, followed by boot at 21:26:50; a second shutdown at 21:31:33 has no subsequent Linux boot recorded until today 11:17:47. Physical off/on versus final-kernel reset remains unproven. Wired NIC/PCIe WOL only is enabled, magic-packet-only; USB wake disabled and RTC alarm empty. No settings changed and no power cycle initiated. Need physical behavior clarification before a coordinated shutdown. Qubit ssh tensor, tensor-lan and tensor-ts now all succeeded. Details: context/sources/TENSOR-POWEROFF-2026-10-17.md. Full mirror synchronization remains deferred; no rollback needed.
