"""Read-only, byte-bounded page snapshot. Never create a store or a lock."""
from datetime import datetime, timezone
import json
import re

from .stats import Events
from .status import bounded_read, STORE_BYTES, EVENT_LINE_BYTES, STATUS_ID, capped_rulings
from .store import Store, call_board

HEADER = 'precedent-log rulings v1'
OUTPUT_BYTES = 64 * 1024
MAX_ROWS = 50
MAX_JOBS = 20


def clean(value, limit):
    return ' '.join(str(value).split())[:limit]


def encode(data):
    return HEADER + '\n' + json.dumps(data, ensure_ascii=True, separators=(',', ':'))


def snapshot():
    try:
        board = call_board()
        if not board:
            return encode({'state': 'no-board'})
        store = Store(board)
        try:
            raw, _ = bounded_read(store.path, STORE_BYTES)
        except FileNotFoundError:
            return encode({'state': 'empty', 'board': board})
        state = store._read(raw)
        if state.warning:
            raise ValueError('damaged store')
        events = Events(board)
        try:
            # Counts require complete history; never present a tail count as total.
            raw, _ = bounded_read(events.path, STORE_BYTES)
        except FileNotFoundError:
            raw = b''
        metrics = {rid: {'jobs': set(), 'veto_count': 0, 'last_veto': None} for rid in state.entries}
        latest = None
        for line in raw.splitlines():
            if len(line) > EVENT_LINE_BYTES:
                raise ValueError('oversize event')
            event = json.loads(line)
            if (not isinstance(event, dict) or type(event.get('v')) is not int or event['v'] != 1
                    or event.get('board') != board or not isinstance(event.get('event'), str)):
                raise ValueError('invalid event')
            if event['event'] not in {'relied', 'veto'}:
                continue
            ids = event.get('ids')
            job = event.get('task_id')
            if (not isinstance(ids, list) or not ids or len(ids) > 20
                    or any(not isinstance(rid, str) or rid not in metrics for rid in ids)
                    or not isinstance(job, str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,128}', job)):
                raise ValueError('invalid citation/veto')
            when = datetime.fromisoformat(event['created_at'].replace('Z', '+00:00'))
            if when.tzinfo is None or when > datetime.now(timezone.utc):
                raise ValueError('invalid timestamp')
            stamp = when.astimezone(timezone.utc).isoformat(timespec='seconds').replace('+00:00', 'Z')
            for rid in set(ids):
                if event['event'] == 'relied':
                    metrics[rid]['jobs'].add(job)
                else:
                    metrics[rid]['veto_count'] += 1
                    metrics[rid]['last_veto'] = max(metrics[rid]['last_veto'] or stamp, stamp)
            if event['event'] == 'veto' and (latest is None or stamp >= latest['at']):
                latest = {'id': ids[0], 'title': clean(state.entries[ids[0]]['question'], 40), 'at': stamp}
        capped = capped_rulings(store)
        data = {'state': 'ready' if state.entries else 'empty', 'board': board,
                'active': len(state.active), 'total': len(state.entries), 'rows': [], 'last_veto': latest,
                'truncated': False, 'cap_reached': bool(capped)}
        for rid, entry in state.entries.items():
            if not STATUS_ID.fullmatch(rid):
                raise ValueError('invalid id')
            metric = metrics[rid]
            jobs = sorted(metric['jobs'])
            row = {'id': rid, 'title': clean(entry['question'], 40),
                   'keys': [clean(key, 80) for key in entry.get('keys', [])[:20]],
                   'status': 'retired' if entry.get('retired') else 'active',
                   'ruling': entry['ruling'][:2000], 'jobs': jobs[:MAX_JOBS], 'cited_count': len(jobs),
                   'veto_count': metric['veto_count'], 'cap_reached': rid in capped, 'last_veto': metric['last_veto']}
            data['rows'].append(row)
            if len(data['rows']) > MAX_ROWS or len(encode(data).encode()) > OUTPUT_BYTES:
                data['rows'].pop()
                data['truncated'] = True
                break
        return encode(data)
    except (OSError, ValueError, KeyError, TypeError, AttributeError, OverflowError):
        return encode({'state': 'unavailable'})
