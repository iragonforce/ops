hl.window_rule({
    name = "sonobus-background",
    match = { class = "^(SonoBus|sonobus)$" },
    workspace = "special:sonobus silent",
    no_initial_focus = true,
})

hl.on("hyprland.start", function()
    hl.exec_cmd(
        "/home/iragonforce/.local/bin/sonobus-session-start"
    )
end)
