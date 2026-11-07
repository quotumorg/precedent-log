"""Page protocol and existing human retirement, with no real profile access."""
import json
from unittest.mock import patch

from support import IsolatedTest
from precedent_log.commands import ruling, rulings
from precedent_log.desktop import HEADER, MAX_ROWS, OUTPUT_BYTES
from precedent_log.stats import Events
from precedent_log.store import Store
from precedent_log.status import STORE_BYTES


class DesktopTests(IsolatedTest):
    def snapshot(self):
        output = rulings('list --json')
        self.assertLessEqual(len(output.encode()), OUTPUT_BYTES)
        self.assertTrue(output.startswith(HEADER + '\n'))
        return json.loads(output.split('\n', 1)[1])

    def saved(self):
        return Store('default').add('schema migrations', 'Use staging.', ['schema', 'migrations'])

    def test_empty_no_board_and_no_writes(self):
        self.assertEqual(self.snapshot(), {'state': 'empty', 'board': 'default'})
        self.assertFalse((self.home / 'precedent-log').exists())
        with patch('precedent_log.desktop.call_board', return_value=None):
            self.assertEqual(self.snapshot(), {'state': 'no-board'})
        with patch('precedent_log.desktop.call_board', side_effect=ValueError):
            self.assertEqual(self.snapshot(), {'state': 'unavailable'})

    def test_list_counts_completed_jobs_and_vetoes_without_writes(self):
        self.saved()
        events = Events('default')
        events.record('citation', 'not-completed', ['P-1'])
        for _ in range(2):
            events.record('relied', 'job-1', ['P-1'])
            events.record('veto', 'job-2', ['P-1'])
        root = self.home / 'precedent-log'
        before = {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in root.iterdir()}
        data = self.snapshot()
        row = data['rows'][0]
        self.assertEqual(row['id'], 'P-1')
        self.assertEqual(row['title'], 'schema migrations')
        self.assertEqual(row['keys'], ['schema', 'migrations'])
        self.assertEqual(row['ruling'], 'Use staging.')
        self.assertEqual(row['jobs'], ['job-1'])
        self.assertEqual(row['cited_count'], 1)
        self.assertEqual(row['veto_count'], 2)
        self.assertIsNotNone(row['last_veto'])
        self.assertEqual(before, {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in root.iterdir()})

    def test_slash_retire_pins_board_and_preserves_replacement_semantics(self):
        self.saved()
        Store('default').add('new guidance', 'Use the new plan.')
        Store('other').add('other', 'Other answer.')
        Events('default').record('relied', 'job-1', ['P-1'])
        with patch('hermes_cli.kanban_db.get_current_board', return_value='other'):
            result = ruling('retire P-1 obsolete --replaced-by P-2 --board default')
        self.assertIn('P-1 retired.', result)
        self.assertIn('Replaced by P-2', result)
        self.assertIn('job-1', result)
        self.assertEqual(Store('other').list()[0]['id'], 'P-1')
        self.assertEqual(self.snapshot()['rows'][0]['status'], 'retired')
        self.assertEqual(self.snapshot()['active'], 1)
        self.assertIn('No active ruling', ruling('retire P-99 obsolete --board default'))
        self.assertIn('Use --board', ruling('retire P-2 obsolete --board ../bad'))

    def test_retire_requires_human_and_error_does_not_mutate(self):
        self.saved()
        with patch('precedent_log.commands.require_human', side_effect=ValueError('human only')):
            self.assertEqual(ruling('retire P-1 obsolete --board default'), 'human only')
        with patch('precedent_log.store.Store.retire', side_effect=OSError('Store lock is busy')):
            self.assertEqual(ruling('retire P-1 obsolete --board default'), 'Store lock is busy')
        self.assertEqual(self.snapshot()['rows'][0]['status'], 'active')

    def test_bounds_unicode_rows_text_and_jobs(self):
        store = Store('default')
        # A verified synthetic snapshot isolates output bounds from log-size bounds.
        from precedent_log.store import Snapshot
        state = Snapshot(entries={f'P-{n}': {'id': f'P-{n}', 'question': '界' * 100,
                'ruling': '界' * 4000, 'keys': ['界' * 100] * 20} for n in range(1, 61)})
        self.saved()
        for n in range(25):
            Events('default').record('relied', f'job-{n}', ['P-1'])
        with patch.object(Store, '_read', return_value=state):
            data = self.snapshot()
        self.assertTrue(data['truncated'])
        self.assertLessEqual(len(data['rows']), MAX_ROWS)
        row = data['rows'][0]
        self.assertEqual(len(row['ruling']), 2000)
        self.assertEqual(len(row['jobs']), 20)
        self.assertEqual(row['cited_count'], 25)
        self.assertEqual(len(row['title']), 40)

    def test_bad_oversize_torn_symlink_history_is_unavailable(self):
        self.saved()
        events = Events('default')
        for raw in [b'bad\n', b'{}', b'x' * (STORE_BYTES + 1),
                    b'{"v":1,"board":"other","event":"veto"}\n']:
            events.path.write_bytes(raw)
            self.assertEqual(self.snapshot()['state'], 'unavailable')
        events.path.unlink()
        target = self.home / 'other'
        target.write_text('')
        events.path.symlink_to(target)
        self.assertEqual(self.snapshot()['state'], 'unavailable')
        events.path.unlink()
        Store('default').path.write_bytes(b'x' * (STORE_BYTES + 1))
        self.assertEqual(self.snapshot()['state'], 'unavailable')

    def test_profile_board_isolation(self):
        self.saved()
        Store('other').add('other question', 'Other answer.')
        with patch('precedent_log.desktop.call_board', return_value='other'):
            self.assertEqual(self.snapshot()['rows'][0]['title'], 'other question')
        with patch('precedent_log.store.home', return_value=self.home / 'other-profile'):
            self.assertEqual(self.snapshot()['state'], 'empty')

    def test_cap_display_from_durable_policy_and_fault_hides(self):
        from precedent_log.gate import decide
        self.saved()
        args = {'reason': 'schema migrations', 'task_id': 'job'}
        self.assertEqual(decide(args)['action'], 'block')
        self.assertFalse(self.snapshot()['cap_reached'])
        self.assertEqual(decide(args)['action'], 'block')
        data = self.snapshot()
        self.assertTrue(data['cap_reached'])
        self.assertTrue(data['rows'][0]['cap_reached'])
        self.assertIn('veto cap reached', rulings('status'))
        self.assertEqual(decide(args)['action'], 'modify')
        (self.home / 'precedent-log/default.policy.json').write_text('{}')
        self.assertEqual(self.snapshot()['state'], 'unavailable')
