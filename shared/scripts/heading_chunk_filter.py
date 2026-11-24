"""Remove Markdown-heading-only vectors without renumbering substantive points.

Used by the three existing Qdrant Markdown indexers after their original
chunking and safety screening. No network access or data mutation occurs here.
"""

import hashlib
import re


HEADING = re.compile(r'#{1,6}[ \t]+\S.*')


def heading_only(text):
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return bool(lines) and all(HEADING.fullmatch(line) for line in lines)


def merge_heading_only_chunks(records, max_chars):
    """Keep original IDs; attach safe heading context within each source file.

    The old generator has already assigned ordinals (including those of
    suppressed headings), so other point identities never shift. Pending
    headings at EOF are discarded; pending headings cannot cross sources.
    """
    pending = []
    source = None
    for point_id, payload in records:
        if source != payload['source']:
            pending = []
            source = payload['source']
        if heading_only(payload['text']):
            pending.append(payload)
            continue
        if pending:
            updated = dict(payload)
            headings = [p['heading'] for p in pending] + [payload['heading']]
            updated['heading'] = ' / '.join(
                heading for index, heading in enumerate(headings)
                if index == 0 or heading != headings[index - 1]
            )
            prefix = ''.join(p['text'] for p in pending)
            if len(prefix) + len(payload['text']) <= max_chars:
                updated['text'] = prefix + payload['text']
                updated['line_start'] = pending[0]['line_start']
            # Otherwise, text/line_start remain unchanged; heading metadata
            # carries context without claiming an unrepresented source line.
            updated['content_sha256'] = hashlib.sha256((
                updated['heading'] + '\n' + str(updated['line_start'])
                + '\n' + updated['text']
            ).encode()).hexdigest()
            payload = updated
            pending.clear()
        yield point_id, payload
