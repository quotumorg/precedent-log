"""Desktop status must observe actual veto records without changing the gate."""
import json
from unittest.mock import patch

from support import IsolatedTest
from precedent_log.commands import rulings
from precedent_log.gate import decide
from precedent_log.stats import Events
from precedent_log.store import Store
from precedent_log.status import HEADER, EVENT_BYTES, EVENT_LINE_BYTES, STORE_BYTES, short_title


class StatusTests(IsolatedTest):
    def saved(self, question='schema migrations'):
        return Store('default').add(question, 'Use staging.', ['schema', 'migrations'])

    def test_missing_store_and_invalid_board_hide_without_writes(self):
        self.assertEqual(rulings('status'), HEADER + '\nrulings=0; no veto yet')
        self.assertFalse((self.home / 'precedent-log').exists())
        with patch('precedent_log.status.call_board', side_effect=ValueError):
            self.assertEqual(rulings('status'), 'Precedent Log status unavailable')

    def test_no_veto_active_count_and_no_writes(self):
        a = self.saved()
        self.saved('other')
        Store('default').retire(a['id'], 'obsolete')
        root = self.home / 'precedent-log'
        before = {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in root.iterdir()}
        self.assertEqual(rulings('status'), HEADER + '\nrulings=1; no veto yet')
        self.assertEqual(before, {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in root.iterdir()})
        self.assertIn('other', rulings())

    def test_actual_veto_latest_and_advisory_does_not_create_veto(self):
        self.saved()
        args = {'reason': 'schema migrations', 'task_id': 'job'}
        self.assertEqual(decide(args, veto_mode='advisory')['action'], 'modify')
        self.assertTrue(rulings('status').endswith('no veto yet'))
        with patch('precedent_log.stats.timestamp', return_value='2026-01-01T12:00:00.123456Z'):
            self.assertEqual(decide(args)['action'], 'block')
        self.assertEqual(rulings('status'), HEADER + '\nrulings=1; veto=P-1; title=schema migrations; at=2026-01-01T12:00:00Z')
        with patch('precedent_log.stats.timestamp', return_value='2026-01-01T12:01:00Z'):
            self.assertEqual(decide(args)['action'], 'block')
        self.assertEqual(decide(args)['action'], 'modify')
        self.assertTrue(rulings('status').endswith('12:01:00Z; veto cap reached'))
        events = Events('default')._read()[0]
        self.assertEqual(sum(e['event'] == 'veto' for e in events), 2)
        Store('default').retire('P-1', 'obsolete')
        self.assertIn('rulings=0; veto=P-1', rulings('status'))

    def test_title_and_output_bounds(self):
        self.saved('schema;\n' + 'migrations ' * 100)
        Events('default').record('veto', 'job', ['P-1'])
        output = rulings('status')
        self.assertEqual(len(output.splitlines()), 2)
        self.assertLessEqual(len(output), 256)
        title = output.split('title=')[1].split('; at=')[0]
        self.assertLessEqual(len(title), 40)
        self.assertNotIn(';', title)
        self.assertNotIn('\n', title)

    def test_bad_and_oversize_veto_records_hide(self):
        self.saved()
        events = Events('default')
        for fields in [{'ids': []}, {'ids': ['P-1'] * 21}, {'ids': ['P-999']},
                       {'created_at': 'bad'}, {'created_at': '9999-01-01T00:00:00Z'},
                       {'padding': 'x' * EVENT_LINE_BYTES}]:
            row = {'v': 1, 'board': 'default', 'event': 'veto', 'ids': ['P-1'],
                   'created_at': '2026-01-01T12:00:00Z', **fields}
            events.path.write_text(json.dumps(row) + '\n')
            self.assertEqual(rulings('status'), 'Precedent Log status unavailable')
        events.path.write_text('{torn')
        self.assertEqual(rulings('status'), 'Precedent Log status unavailable')

    def test_bounded_tail_keeps_latest_and_does_not_fabricate_no_veto(self):
        self.saved()
        events = Events('default')
        row = json.dumps({'v': 1, 'board': 'default', 'event': 'uncited'}) + '\n'
        events.path.write_text(row * (EVENT_BYTES // len(row) + 2))
        self.assertEqual(rulings('status'), 'Precedent Log status unavailable')
        Events('default').record('veto', 'job', ['P-1'])
        self.assertIn('veto=P-1', rulings('status'))

    def test_damaged_oversize_or_symlink_store_hides(self):
        self.saved()
        store = Store('default')
        original = store.path.read_bytes()
        for raw in [b'bad\n', original[:-1], b'x' * (STORE_BYTES + 1)]:
            store.path.write_bytes(raw)
            self.assertEqual(rulings('status'), 'Precedent Log status unavailable')
        store.path.unlink()
        target = self.home / 'other'
        target.write_bytes(original)
        store.path.symlink_to(target)
        self.assertEqual(rulings('status'), 'Precedent Log status unavailable')

    def test_board_and_profile_isolation(self):
        self.saved()
        Events('default').record('veto', 'job', ['P-1'])
        Store('other').add('other', 'another answer')
        with patch('precedent_log.status.call_board', return_value='other'):
            self.assertEqual(rulings('status'), HEADER + '\nrulings=1; no veto yet')
        with patch('precedent_log.store.home', return_value=self.home / 'empty-profile'):
            self.assertEqual(rulings('status'), HEADER + '\nrulings=0; no veto yet')

    def test_word_boundary_titles(self):
        for question, expected in [
            ('staging or prod DB for the schema migration?', 'staging or prod DB for the schema…'),
            ('which httpx version for the dependency upgrade?', 'which httpx version for the dependency…'),
            ('a' * 40, 'a' * 40), ('a' * 41, '…'),
            ('a' * 39 + ' next word', 'a' * 39 + '…'),
            ('short;\nquestion', 'short question'),
        ]:
            self.assertEqual(short_title(question), expected)
            self.assertLessEqual(len(short_title(question)), 40)

    def test_missing_event_and_policy_files_are_optional_and_read_only(self):
        self.saved()
        root = self.home / 'precedent-log'
        self.assertFalse(Events('default').path.exists())
        self.assertFalse((root / 'default.policy.json').exists())
        before = {p.name: p.read_bytes() for p in root.iterdir()}
        self.assertEqual(rulings('status'), HEADER + '\nrulings=1; no veto yet')
        self.assertEqual(before, {p.name: p.read_bytes() for p in root.iterdir()})
        with patch('precedent_log.status.bounded_read', side_effect=PermissionError):
            self.assertEqual(rulings('status'), 'Precedent Log status unavailable')

    def test_broken_links_remain_unavailable(self):
        self.saved()
        store = Store('default')
        for path in [store.path, Events('default').path, store.path.with_name('default.policy.json')]:
            original = path.read_bytes() if path.exists() else None
            path.unlink(missing_ok=True)
            path.symlink_to(self.home / 'missing')
            self.assertEqual(rulings('status'), 'Precedent Log status unavailable')
            path.unlink()
            if original is not None:
                path.write_bytes(original)
