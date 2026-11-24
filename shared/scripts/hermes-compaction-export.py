#!/usr/bin/env python3
"""Read completed main-profile compactions and extract conservative historical findings.

No database writes. Summary text is untrusted; ambiguous or sensitive findings
are excluded, and retained findings are explicitly historical, not live facts.
Use --help for the protected review workflow. The Qdrant dispatcher imports
build_findings; this module itself never contacts Qdrant.
"""

import argparse
import hashlib
import re
import sqlite3
import statistics
import subprocess
import uuid
from collections import Counter, defaultdict
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

EXTRACT = (
    "Completed Actions",
    "Errors & Fixes",
    "Key Decisions",
    "Resolved Questions",
)

HEADING = re.compile(r"^[ \t]{0,3}(#{1,6})[ \t]+(.+?)\s*$")
FENCE = re.compile(r"^[ \t]{0,3}(`{3,}|~{3,})")


def digest(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def sections(content):
    """Yield Markdown sections, preserving repeated headings and nesting."""
    lines = content.splitlines(keepends=True)
    headings = []
    fence_character = None
    fence_length = 0

    for position, line in enumerate(lines):
        marker = FENCE.match(line)

        if marker:
            token = marker.group(1)

            if fence_character is None:
                fence_character = token[0]
                fence_length = len(token)
            elif (
                token[0] == fence_character
                and len(token) >= fence_length
            ):
                fence_character = None
                fence_length = 0

            continue

        if fence_character is not None:
            continue

        match = HEADING.match(line)

        if match:
            title = re.sub(
                r"\s+#+\s*$", "", match.group(2)
            ).strip()

            headings.append((
                position,
                len(match.group(1)),
                title,
            ))

    for ordinal, (start, level, title) in enumerate(headings):
        end = len(lines)

        for next_start, next_level, _ in headings[ordinal + 1:]:
            if next_level <= level:
                end = next_start
                break

        yield ordinal, title, "".join(lines[start + 1:end]).strip()


def fetch_candidates(database, strict=True):
    uri = "file:" + quote(str(database), safe="/") + "?mode=ro"

    with closing(sqlite3.connect(uri, uri=True, timeout=10)) as connection:
        connection.execute("PRAGMA query_only=ON")
        # Both SELECTs must observe one SQLite snapshot while Hermes is writing.
        connection.execute("BEGIN")

        boundaries = {
            row[0] for row in connection.execute("""
                SELECT id
                FROM sessions
                WHERE end_reason = 'compression'
            """)
        }

        rows = connection.execute("""
            SELECT p.id, c.id, m.id, m.content
            FROM sessions p
            JOIN sessions c ON c.parent_session_id = p.id
            JOIN messages m ON m.session_id = c.id
            WHERE p.end_reason = 'compression'
              AND m._compressed_summary = 1
            ORDER BY p.ended_at, p.id, c.started_at, m.id
        """).fetchall()

    candidates = defaultdict(list)

    for parent, child, message_id, content in rows:
        if not isinstance(content, str):
            raise RuntimeError("Non-text compaction summary")

        candidates[parent].append((
            child, message_id, content
        ))

    if strict and set(candidates) != boundaries:
        raise RuntimeError(
            "Compaction lineage incomplete: "
            f"{len(candidates)}/{len(boundaries)}"
        )

    selected = []

    for parent, entries in candidates.items():
        unique = {digest(content) for _, _, content in entries}

        if len(unique) != 1:
            raise RuntimeError(
                "Ambiguous summary candidates for a compaction boundary"
            )

        child, message_id, content = entries[0]
        selected.append((
            parent, child, message_id, content
        ))

    return len(boundaries), selected


ITEM = re.compile(r"(?m)^(?:\s*(?:[-*]|\d+[.)])\s+)")
PATH = re.compile(r"(?:docs|shared|hosts|man)/[A-Za-z0-9_./-]+")
PERSONAL = re.compile(
    r"(?i)(?:[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}|\b\+?\d[\d ().-]{9,}\d\b|"
    r"/home/(?!iragonforce/ops/)[^\s`]+|"
    r"\b(?:password|secret|token|credential|api.?key|private.?key|session.?cookie|"
    r"bank|finance|financial|statement|wealthfolio|receipt|cibc|tfsa|credit.card|"
    r"authentication|oauth|login)\b|"
    r"-----BEGIN |\b(?:bearer|basic)\s+[A-Za-z0-9+/=]{12,})"
)
DISCARD = re.compile(
    r"(?i)\b(?:user correction|assistant reported|tool.call limit|"
    r"unverified|not verified|pending|proposed|planned|todo|"
    r"earlier attempt|still need|could not|should not infer|"
    r"\bREAD\b|\bCREATED\b|\bDOCUMENTED\b|\bINSPECTED\b)\b"
)


def tracked_paths(repo):
    """Only public Git-tracked files can supply corroboration candidates."""
    result = subprocess.run(
        ["git", "-C", str(repo), "ls-files", "-z"],
        capture_output=True, check=True,
    )
    return set(result.stdout.decode().strip("\0").split("\0"))


def split_findings(body):
    """Extract individual top-level list items; never split arbitrarily by size."""
    markers = list(ITEM.finditer(body))
    if not markers or body[:markers[0].start()].strip():
        return []
    return [body[mark.end():markers[i+1].start() if i+1 < len(markers) else len(body)].strip()
            for i, mark in enumerate(markers)]


def build_findings(candidate, repo, scanners):
    """Return safe, independently scoped records and quarantine reason counts.

    Original agent claims are never promoted to verified current configuration.
    A Git reference is a traceability gate, not a content verification claim.
    """
    parent, child, message_id, content = candidate
    allowed = tracked_paths(repo)
    accepted, quarantined = [], Counter()
    for ordinal, section, body in sections(content):
        if section not in EXTRACT or not body:
            continue
        for item_number, raw in enumerate(split_findings(body)):
            # Reject code blocks and compound/nested list items rather than
            # embedding an arbitrary portion of an oversized incident.
            text = re.sub(r"\s+", " ", raw).strip()
            if not 75 <= len(text) <= 750 or "```" in raw or "\n  - " in raw:
                quarantined['structure'] += 1
                continue
            if "\x00" in text or PERSONAL.search(text) or any(s.search(text) for s in scanners):
                quarantined['sensitive'] += 1
                continue
            if DISCARD.search(text):
                quarantined['ambiguous'] += 1
                continue
            refs = sorted({m.group(0).rstrip('.,;:')
                           for m in PATH.finditer(text)} & allowed)
            if not refs:
                quarantined['no_git_reference'] += 1
                continue
            # A finding must be a single item with no unrelated next subject.
            if re.search(r"(?:^|[.;])\s*(?:Separately|Unrelated|Meanwhile|Also on)\b", text, re.I):
                quarantined['mixed_topics'] += 1
                continue
            text = re.sub(r"\s*\[tools?:[^\]]+\]$", "", text).strip()
            outcome = text.split(" — ", 1)[-1].split(",", 1)[0].split(";", 1)[0]
            title = re.sub(r"[`*_#]", "", outcome)[:100].rsplit(" ", 1)[0].strip(" .;:-")
            if len(title) < 15:
                quarantined['structure'] += 1
                continue
            content_hash = digest(text)
            point_id = str(uuid.uuid5(uuid.NAMESPACE_URL,
                f"hermes_session:{parent}:{child}:{message_id}:{ordinal}:{item_number}"))
            accepted.append((point_id, {
                'origin': 'hermes_session',
                'source': f'hermes-compaction/{parent}/{child}/{message_id}',
                'parent_session_id': parent,
                'compaction_session_id': child,
                'summary_message_id': message_id,
                'section': section,
                'item_ordinal': item_number,
                'topic': title,
                'heading': title,
                'text': text,
                'evidence_paths': refs,
                'content_sha256': content_hash,
                'kind': 'historical_technical_finding',
                'authority': 'agent_summary_historical_unverified',
                'verification': 'git_path_referenced_not_content_verified',
                'confidence': 'low',
                'historical_only': True,
            }))
    return accepted, quarantined


def observation_dates(database):
    uri = "file:" + quote(str(database), safe="/") + "?mode=ro"
    with closing(sqlite3.connect(uri, uri=True, timeout=10)) as connection:
        connection.execute("PRAGMA query_only=ON")
        return {session: datetime.fromtimestamp(ended, timezone.utc).date().isoformat()
                for session, ended in connection.execute(
                    "SELECT id, ended_at FROM sessions WHERE end_reason='compression' AND ended_at IS NOT NULL")}


def audit(candidates):
    counts = Counter()
    sizes = defaultdict(list)
    identifiers = set()
    oversized = Counter()
    repeated_bodies = Counter()
    body_hashes = set()
    examples = []

    for parent, child, message_id, content in candidates:
        for ordinal, title, body in sections(content):
            if title not in EXTRACT or not body:
                continue

            body_hash = digest(re.sub(r"\s+", " ", body))

            identity = digest(
                f"hermes-compaction-v1\0{parent}\0{child}\0"
                f"{message_id}\0{ordinal}\0{title}\0{body_hash}"
            )

            if identity in identifiers:
                raise RuntimeError("Candidate identity collision")

            identifiers.add(identity)

            if body_hash in body_hashes:
                repeated_bodies[title] += 1

            body_hashes.add(body_hash)

            size = len(body.encode("utf-8"))
            counts[title] += 1
            sizes[title].append(size)

            if size > 10000:
                oversized[title] += 1

            if len(examples) < 5:
                examples.append((identity[:16], title, size))

    print("\n=== SELECTED SECTIONS ===")

    for title in EXTRACT:
        values = sizes[title]

        print(
            f"{title}: "
            f"count={counts[title]} "
            f"median_bytes="
            f"{statistics.median(values) if values else 0:.0f} "
            f"max_bytes={max(values, default=0)} "
            f"oversized={oversized[title]}"
        )

    print("\n=== EXPORT MANIFEST ===")
    print("Candidates:", len(identifiers))
    print("Source bytes:", sum(map(sum, sizes.values())))
    print("Repeated normalized bodies:", sum(repeated_bodies.values()))

    print("\nFirst five candidate identifiers:")

    for identifier, title, size in examples:
        print(f"  {identifier} | {title} | {size} bytes")

    print("\n=== SAFETY ===")
    print("Database writes: none")
    print("Summary contents displayed: none")
    print("Files exported by audit: none")
    print("Qdrant writes: none")
    print("Credential review: not yet performed")
    print("Semantic deduplication: not yet performed")



def stage_candidate(candidate, database):
    """Stage selected sections for review; never write to Qdrant."""
    import importlib.util
    import os
    import stat

    if os.geteuid() != 0:
        raise RuntimeError("Protected staging requires root")

    expected_db = Path(
        "/srv/containers/data/hermes/data/state.db"
    )

    if database.resolve(strict=True) != expected_db:
        raise RuntimeError("Unexpected session database")

    scanners = []

    for filename in ("qdrant-memory.py", "git-snapshot-index.py"):
        scanner_path = Path(__file__).parent / filename

        if not scanner_path.is_file():
            raise RuntimeError("Missing scanner: " + filename)

        spec = importlib.util.spec_from_file_location(
            "hermes_scan_" + filename.replace("-", "_").replace(".", "_"),
            scanner_path,
        )

        if spec is None or spec.loader is None:
            raise RuntimeError("Unable to load credential scanner")

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        scanner = getattr(module, "SENSITIVE", None)

        if not isinstance(scanner, type(re.compile(""))):
            raise RuntimeError("Invalid credential scanner")

        scanners.append(scanner)

    parent, child, message_id, content = candidate

    records = []
    excluded = 0

    for ordinal, title, body in sections(content):
        if title not in EXTRACT or not body:
            continue

        if "\x00" in body or any(
            scanner.search(body) for scanner in scanners
        ):
            excluded += 1
            continue

        normalized = re.sub(r"\s+", " ", body).strip()
        body_hash = digest(normalized)

        identity = digest(
            f"hermes-compaction-v1\0{parent}\0{child}\0"
            f"{message_id}\0{ordinal}\0{title}\0{body_hash}"
        )

        document = (
            "# UNREVIEWED Hermes memory candidate\n\n"
            "Proposed origin: `hermes_session`\n\n"
            "Authority: `unverified_agent_summary`\n\n"
            f"Parent session: `{parent}`\n\n"
            f"Continuation session: `{child}`\n\n"
            f"Summary message: `{message_id}`\n\n"
            f"Section ordinal: `{ordinal}`\n\n"
            f"Content SHA-256: `{body_hash}`\n\n"
            "---\n\n"
            f"## {title}\n\n"
            f"{body.rstrip()}\n"
        ).encode("utf-8")

        if len(document) > 256 * 1024:
            raise RuntimeError("Oversized review document")

        records.append((identity[:24] + ".md", document))

    if not records:
        raise RuntimeError("No eligible sections to stage")

    stage = expected_db.parent / "memory-export-review"

    if stage.is_symlink():
        raise RuntimeError("Staging directory is a symlink")

    if not stage.exists():
        stage.mkdir(mode=0o700)

    info = stage.stat()

    if (
        not stage.is_dir()
        or info.st_uid != 0
        or stat.S_IMODE(info.st_mode) != 0o700
    ):
        raise RuntimeError(
            "Staging directory must be root-owned and 0700"
        )

    pending = []
    unchanged = 0

    for filename, document in records:
        target = stage / filename

        if target.is_symlink():
            raise RuntimeError("Staged file is a symlink")

        if target.exists():
            info = target.stat()

            if (
                not target.is_file()
                or info.st_uid != 0
                or stat.S_IMODE(info.st_mode) != 0o600
                or target.read_bytes() != document
            ):
                raise RuntimeError("Existing staged file differs")

            unchanged += 1
        else:
            pending.append((target, document))

    for target, document in pending:
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        flags |= getattr(os, "O_NOFOLLOW", 0)

        fd = os.open(target, flags, 0o600)

        with os.fdopen(fd, "wb") as output:
            output.write(document)
            output.flush()
            os.fsync(output.fileno())

    print("\n=== PROTECTED REVIEW STAGING ===")
    print("Directory:", stage)
    print("New files:", len(pending))
    print("Unchanged files:", unchanged)
    print("Credential-filter exclusions:", excluded)
    print("Compactions staged: 1")
    print("Review status: UNREVIEWED")
    print("Qdrant writes: 0")

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--db",
        type=Path,
        default=Path("/opt/data/state.db"),
    )

    parser.add_argument(
        "--stage-number",
        type=int,
        default=None,
        help="Stage one 1-based compaction for review",
    )
    args = parser.parse_args()

    if not args.db.is_file():
        parser.error(f"Session database missing: {args.db}")

    boundaries, candidates = fetch_candidates(args.db)

    print("=== HERMES COMPACTION EXPORT DRY RUN ===")
    print("Completed boundaries:", boundaries)
    print("Distinct summary candidates:", len(candidates))

    audit(candidates)

    if args.stage_number is not None:
        if not 1 <= args.stage_number <= len(candidates):
            parser.error("Invalid compaction number")

        stage_candidate(
            candidates[args.stage_number - 1],
            args.db,
        )

    print("\nPASS: Compaction exporter completed")


if __name__ == "__main__":
    main()
