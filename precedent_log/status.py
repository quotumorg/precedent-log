"""Bounded, read-only Desktop protocol over existing rulings and gate events."""

from datetime import datetime, timezone
import json
import os
import re
import unicodedata

from .stats import Events
from .store import Store, call_board

HEADER = 'precedent-log status v1'
STORE_BYTES = 1024 * 1024
EVENT_BYTES = 64 * 1024
EVENT_LINE_BYTES = 4096
TITLE_CHARS = 40
OUTPUT_CHARS = 256
STATUS_ID = re.compile(r'P-[1-9][0-9]{0,8}\Z')


def bounded_read(path, limit, tail=False):
    # No lock creation or recovery: status never writes, including on first use.
    if path.parent.is_symlink():
        raise ValueError('symlink store')
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, 'rb') as stream:
        import stat
        info = os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode):
            raise ValueError('nonregular store')
        start = max(0, info.st_size - limit) if tail else 0
        stream.seek(start)
        raw = stream.read(limit + 1)
        if len(raw) > limit or (raw and not raw.endswith(b'\n')):
            raise ValueError('oversize or incomplete store')
        # Discard the first partial line even if the offset happened to align.
        return (raw.split(b'\n', 1)[-1] if start else raw), bool(start)


def last_veto(events, entries):
    if not events.path.exists() and not events.path.is_symlink():
        return None
    raw, truncated = bounded_read(events.path, EVENT_BYTES, tail=True)
    for line in reversed(raw.splitlines()):
        if len(line) > EVENT_LINE_BYTES:
            raise ValueError('oversize event')
        row = json.loads(line)
        if (not isinstance(row, dict) or type(row.get('v')) is not int or row['v'] != 1
                or row.get('board') != events.board or not isinstance(row.get('event'), str)):
            raise ValueError('invalid event')
        if row['event'] != 'veto':
            continue
        ids = row.get('ids')
        if (not isinstance(ids, list) or not ids or len(ids) > 20
                or any(not isinstance(rid, str) or not STATUS_ID.fullmatch(rid) for rid in ids)):
            raise ValueError('invalid veto ids')
        # One representative ruling when the issued veto named several candidates.
        rid = ids[0]
        question = entries[rid]['question']
        title = ''.join(c if c != ';' and not unicodedata.category(c).startswith('C') else ' '
                        for c in question)
        title = ' '.join(title.split())[:TITLE_CHARS].strip()
        if not title:
            raise ValueError('empty title')
        stamp = row.get('created_at')
        if not isinstance(stamp, str) or len(stamp) > 32:
            raise ValueError('invalid timestamp')
        when = datetime.fromisoformat(stamp.replace('Z', '+00:00'))
        if when.tzinfo is None or when > datetime.now(timezone.utc):
            raise ValueError('invalid timestamp')
        stamp = when.astimezone(timezone.utc).isoformat(timespec='seconds').replace('+00:00', 'Z')
        return f'veto={rid}; title={title}; at={stamp}'
    if truncated:
        raise ValueError('older veto history unavailable')
    return None


def status():
    try:
        store = Store(call_board())
        raw, _ = bounded_read(store.path, STORE_BYTES)
        state = store._read(raw)
        if state.warning or len(state.active) > 999999999:
            raise ValueError('rulings unavailable')
        veto = last_veto(Events(store.board), state.entries)
        output = f'{HEADER}\nrulings={len(state.active)}; {veto or "no veto yet"}'
        if len(output) > OUTPUT_CHARS:
            raise ValueError('status too long')
        return output
    except (OSError, ValueError, KeyError, TypeError, OverflowError):
        return 'Precedent Log status unavailable'
