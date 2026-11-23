# Bitwarden desktop SSH agent on macOS

Use current official Bitwarden docs before changing settings: https://bitwarden.com/help/ssh-agent/ and https://bitwarden.com/help/about-ssh/. UI labels and socket paths vary by installation type.

## Inspect before migrating

1. On the actual Mac, check desktop app installation source/version, running state, socket existence, current shell's `SSH_AUTH_SOCK`, and `ssh -G <alias>` for IdentityFile, IdentityAgent, IdentitiesOnly, HostKeyAlias and ProxyCommand. A remote noninteractive SSH shell's environment is not proof of the user's interactive shell configuration.
2. List public keys only: `cd ~/.ssh && ls -la *.pub`. Do not use `ls -la | grep *.pub`: shell globbing changes grep's arguments. A `.pub` file alone neither proves that its corresponding private file is usable nor that it belongs in the vault.
3. Point only the probe's environment at the verified Bitwarden socket: `SSH_AUTH_SOCK=<socket> ssh-add -L`; do not print the returned public key text unnecessarily. Compare public-key type+blob to each relevant existing `.pub` file and report match booleans or fingerprints. An agent listing proves availability, not use by SSH.

## Import and approval choices

- Bitwarden's New → SSH key form defaults to generating a new key; existing-key import is a separate "Import key from clipboard" icon. User copies the PRIVATE key locally (OpenSSH/PKCS#8 including BEGIN/END lines) and performs vault import/unlock in the local GUI; never transfer it through this agent's tools or chat. Clear the clipboard afterward, accounting for macOS shared/universal clipboard exposure. Alternatively generate a fresh Bitwarden key and add only its public key to targets while retaining old authorized keys for rollback.
- Bitwarden agent's authorization modes are Always (default), Remember until vault is locked, and Never. Explain that unlocking a locked vault may still be needed. Prefer Remember until vault is locked when user wants fewer prompts without permanent silent signing. Agent forwarding can prompt separately; do not enable forwarding casually.
- Socket path differs: ordinary .dmg app usually `~/.bitwarden-ssh-agent.sock`; Mac App Store app usually `~/Library/Containers/com.bitwarden.desktop/Data/.bitwarden-ssh-agent.sock`. Verify live path instead of assuming; set `SSH_AUTH_SOCK` only after agent-only tests.
- Bitwarden's agent does not offer arbitrary `ssh-add` key management or per-host key selection. With multiple vault keys, constrain offers using the matching public-only IdentityFile and IdentitiesOnly, then inspect `ssh -G` and server auth results.

## Prove signing without risking existing access

For each target, perform a separate bounded `ssh -F /dev/null -vv -o BatchMode=yes -o StrictHostKeyChecking=yes -o ConnectTimeout=... -o IdentityAgent=<Bitwarden-socket> -o IdentitiesOnly=yes -i ~/.ssh/<matching>.pub -o HostKeyAlias=<verified-host-identity> -o UserKnownHostsFile=~/.ssh/known_hosts -o ProxyCommand='<existing-route-helper> <target> 22' user@<verified-address> hostname`. Adapt route arguments to the inspected config; do not paste private key paths as `-i` in this isolation probe. Capture only offering/acceptance/authentication debug lines, not full verbose output. Require `explicit agent`, server acceptance and `Authenticated ... using publickey` along with the expected remote hostname. A successful default alias is only a connectivity baseline; it may use a disk key. If a probe stalls, inspect partial debug output and coordinate any Bitwarden approval window; do not present the timeout as proof of failure or success. Test direct/automatic routes as relevant, then stage persistent IdentityAgent/shell environment changes with a rollback copy and confirm normal fresh SSH while old access remains available.
