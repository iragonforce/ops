# Compose your own Paperclip shortcuts on Qubit

No shortcut was created or imported. The prepared command uses Qubit's existing SSH identity. It never embeds an API key in a shortcut. A request creates a current Paperclip task assigned to the coordinator; the reply confirms submission rather than waiting for the task to finish.

## Ask Paperclip

Create a shortcut named **Ask Paperclip** with these actions in order:

1. **Ask for Input**
   - Input type: **Text**.
   - Prompt: **What should Paperclip do?**
2. **Run Shell Script**
   - Shell: `/bin/zsh`.
   - Input: the **Provided Input** result from the previous action.
   - Pass input: **to stdin**.
   - Script:

   ```sh
   /Users/iragonforce/.local/bin/paperclip-request ask
   ```
3. **Show Result**, using the shell script's output. You can use **Speak Text** instead for an explicitly spoken response.

Run it once from the Shortcuts app. If macOS blocks scripting actions, enable **Allow Running Scripts** in Shortcuts → Settings → Advanced. Then activate Siri on Qubit and say **Ask Paperclip**.

## Paperclip Status

Create a second shortcut named **Paperclip Status**:

1. **Run Shell Script**, shell `/bin/zsh`:

   ```sh
   /Users/iragonforce/.local/bin/paperclip-request status
   ```
2. **Show Result**, using the script output.

Say **Paperclip Status** to Siri on Qubit.

## Checks and limits

- `paperclip-request status` successfully reached Nexus and reported Hermes, coordinator and Tensor Ollama idle on 2026-10-17.
- Voice invocation and the manually composed shortcuts have not been checked.
- The task-submission branch is configured but was not exercised by creating an artificial task.
- This recipe uses macOS's local shell action and is intended to run on Qubit. An iPhone needs a separate SSH-based shortcut rather than Qubit's local filesystem path.
- Keep credentials out of spoken requests and task descriptions. Provide private file paths when a task requires a credential.
- Nexus-side helper: `/srv/containers/data/paperclip/tools/qubit-control.ts`.
- Authentication uses a one-minute in-memory board credential for the existing administrator, revoked in finally. No persistent Paperclip board key is stored on Qubit.

## Apple documentation

- [Ask for Input](https://support.apple.com/guide/shortcuts-mac/use-the-ask-for-input-action-apd68b5c9161/mac)
- [Run shortcuts with Siri](https://support.apple.com/guide/shortcuts-mac/run-shortcuts-with-siri-apd07c25bb38/mac)

## Rollback

Remove the local `~/.local/bin/paperclip-request` helper and Nexus's `qubit-control.ts` if this integration is no longer wanted. Delete only the shortcuts you manually created. Existing SSH keys, aliases and permissions were preserved.
