# Automatic Git-backed project documentation indexing

Date: November 25, 2026. Objective: after a completed project is documented and committed in the public `iragonforce/ops` repository, automatically embed its Markdown in the existing Qdrant collection without copying raw private chats, indexing drafts, changing other origins or adding another scheduler.

## Scope and design

- Add `sync-ops` to the existing Nexus `qdrant-memory.py` dispatcher and append one unprivileged post-step to the existing hourly `qdrant-memory.service`. The existing inbox, compaction and settled-chat steps remain in their prior order and retain their semantics.
- Check that the Nexus `~/ops` directory is the actual Git root and that no `.md` file is modified, staged, untracked or ignored before allowing the existing `homelab-index-ops.py` to scan its working tree. The Git SHA and Markdown cleanliness are checked again after successful indexing; a concurrent edit/commit fails visibly so a later run can reconcile. An unrelated dirty non-Markdown host config does not block indexing. No GitHub fetch, auto-merge, reset, private checkout access or remote-push trigger is introduced.
- Run the existing idempotent `origin=ops` indexer. It hashes source/heading/line/text, embeds only changed/new passages with the existing Tensor Ollama model, waits for Qdrant upserts and reads back hashes. It retains stale points for review; no automatic deletion or collection-wide replacement.
- Git-push-only projects are not automatically present in the Nexus local checkout. Complete the verified project closeout by fast-forwarding that checkout without overwriting dirty work. The next hourly service run can then reconcile the new committed Markdown; a manually started *existing service* may verify the path sooner. This is not GitHub Pages website crawling or automatic indexing of arbitrary repositories.

## Staging checks and deployment gates

- On the task branch based on the then-current public `origin/consolidate` at `e104b1882a11ee8e58a3b26ecb5ec587d88520a1`, five new isolated Git-fixture regressions passed (clean tracked document with unrelated dirty non-Markdown, staged/modified/untracked/ignored Markdown refusal, mid-run edit retry, missing repo refusal and dry-run isolation). Five chat selector regressions and ten heading-parser regressions also passed; code compiled and `git diff --check` passed.
- At initial Nexus readback the existing service returned `Result=success`, was inactive between hourly invocations, and the timer was active. The Nexus checkout was at `23dc65f2971536244ac92453761822144c43538b` with only an unrelated dirty `hosts/nexus/files/etc/ssh/sshd_config`. Preserve it. Before deployment, verify the live installed unit matches prior Git source, publish the tested source, fast-forward only safe source changes, validate the staged unit with `systemd-analyze verify`, and read back exact installed files.
- Live acceptance still pending at this staging revision: manually run the existing service once after installation and confirm inbox, compaction, chat and ops post-step results; confirm a changed `origin=ops` point for this exact committed document through Qdrant hash readback and MCP search/read; repeat with no new embeddings; observe the timer retained. Do not claim completed ingestion before these checks.

## Recovery

If ops ingestion needs to stop, remove only the final `ExecStartPost` for `sync-ops` from the Git-owned Nexus unit, install/verify/reload it and restart the existing timer/path in their prior states. Retain the inbox, compaction and chat post-steps, collection, other origins, existing `ops` points and any private checkpoints. Source and the prior unit are recoverable from Git history; no rollback deletes Qdrant points without separately reviewed exact IDs. The unit fails on Git/Qdrant errors and is retryable; an uncommitted Markdown draft causes only an `OPS SKIP`, leaving other steps successful.
