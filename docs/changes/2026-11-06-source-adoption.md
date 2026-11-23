# Three-host source adoption and documentation

Objective: establish identifiable source ownership and a reviewable deployment path without changing working service locations.

Hosts: qubit, tensor, nexus. Project: private `iragonforce/ops`. Source/deployment mapping: `inventory/deployments.json`; reviewed ownership and consumer evidence: `inventory/current.json`; original audit remains immutable under `inventory/audit-2026-11-06`.

Captured existing non-secret scripts/configuration and dependency sources. Excluded credentials, package entry points, generated dependencies and vendor code. Consolidated byte-identical script sources while preserving host variants and installed paths. Added introductory documentation, safe help handling where absent, and host-specific manual pages. Existing native/forwarded help remains intact. Updated the existing installer to preview by default, require an explicit apply selection, refuse drift, preserve ownership/modes/links and avoid service reloads.

Validation: 134 edited script sources passed Python AST or shell syntax checks. Trivy secret scan reported zero findings after source adoption. This is syntax and secret-pattern evidence, not proof of every existing script's hardware or service behavior. Deployment results are recorded separately after readback.

Rollback: private backup branch `unified-infra-2026-11-06`, `source-before/`, plus its mapping and this repository's history. No database, credential or raw session transcript is included.

Deliberate compatibility decision: retain established host-prefixed service entry points and host shortcuts. Their consumers make blind renaming unnecessary risk; future new utilities use functional names. Retained mixed backups are classified in `inventory/backups.md`; no unverified deletion is justified by age alone.

Commit linkage: the commit containing this record and subsequent deployment record, discoverable with `git log --follow`.

Phase 2 completion: commit 3234624 adds the remaining integration helpers, 41 functional source renames and the owner’s revised AGENTS.md. A total of 182 script sources passed syntax checks; 207 host manual pages are installed. Installed compatibility paths remain unchanged. Per-target atomic deployment readback passed on all three hosts. `man -w tmux-ensure-layout` resolves the installed manual on each host. Only three named managed Syncthing folders per host are paused; previous pause states are in the private backup branch. No service reload or desktop interruption occurred. Host-specific Git clones fetch over existing SSH from Nexus; Nexus pushes to private GitHub.
