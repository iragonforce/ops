# Qubit context-mode hook cache repair — 2026-10-29

User reported: Hook failed, unsupported plugin entry type at context-mode 1.0.169/node_modules/.bin/esbuild.

Observed: the reported entry was an npm symlink to ../esbuild/bin/esbuild. The plugin tree contained 14 symlinks, all executable entries inside node_modules/.bin directories, including a nested tsx dependency. The error is consistent with Codex plugin-cache preparation rejecting these entry types before executing the hook.

Changed only the installed Qubit context-mode 1.0.169 cache: replaced all 14 symlinks with regular executable shell launchers that exec the original relative targets. Added plugin-local .npmrc bin-links=false to prevent npm from recreating symbolic links during dependency installation in this version. No hook trust, global npm, credential, or homelab authentication settings changed.

Operational checks: zero symlinks or other non-regular/non-directory entries remain; esbuild 0.27.7, TypeScript 5.9.3 and tsx 4.23.15 launch successfully. Direct benign PreToolUse invocation exited 0, produced valid hookSpecificOutput, and no stderr. Formal tests were not run. Full application lifecycle hook success across a fresh session was not independently observed.

Rollback: python3 /Users/iragonforce/.local/state/context-mode-hook-repair/20261029-203520/rollback.py
The saved rollback.json contains original link targets and the previous plugin-local npm settings state.

Pending: plugin upgrades replace the versioned cache; recheck entry types if this error recurs. bin-links=false prevents new npm executable links, so newly added package commands may need regular launchers if used. Existing 14 launchers retain the original commands.
