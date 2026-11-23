# Neovim tree, quit confirmation and safe swap recovery

Date: 2026-11-18

## Objective
Keep NvimTree at 34 columns, provide :TT and <leader>tt,
use native confirmation for modified buffers, and expose
non-destructive recovery of abandoned modified swap files.

## Source
Shared: shared/unified/nvim
Qubit overrides: hosts/qubit/files/.config/nvim/lua
Deployment registry: inventory/deployments.json

## Completed before this rollout
- Qubit native/headless and isolated recovery checks
- Git source published as 1967b30
- 35 matching Qubit standalone files registered
- Historical deployment records preserved

## Deployment policy
- Preserve Qubit's native clipboard and iCloud vault settings.
- Deploy only explicitly selected files on Nexus and Tensor.
- Refuse unexpected edits, symlinks and conflicting baselines.
- Keep rollback copies of live files before replacement.
- Do not delete original swap files or legacy configurations.

## Validation
Run the separate nvim-test.sh on each host.
Interactive desktop checks are deferred until explicitly run.

## Recovery
Use the Git revision immediately preceding each deployment
commit for source rollback. Live originals are saved in a
private per-deployment directory under ~/.local/state/ops/.
Inspect original and current file hashes before restoring.
