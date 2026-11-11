"""Page protocol and existing human retirement, with no real profile access."""
import json
from unittest.mock import patch

from support import IsolatedTest
from precedent_log.commands import ruling, rulings
from precedent_log.desktop import HEADER, MAX_ROWS, MAX_TIMELINE_JOBS, OUTPUT_BYTES
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

    def test_timeline_save_cite_explain_retire_and_receipt(self):
        with patch('precedent_log.store.timestamp', return_value='2026-01-01T10:00:00Z'):
            result = ruling('add schema migrations => Use staging. [keys: schema, migrations]',
                            platform='desktop', session_key='session-example')
        self.assertEqual(result, 'Added P-1')
        events = Events('default')
        with patch('precedent_log.stats.timestamp', return_value='2026-01-01T11:00:00Z'):
            events.record('citation', 'card-1', ['P-1'], veto=True)
            events.record('justification', 'card-2', ['P-1'])
            events.record('relied', 'card-1', ['P-1'])
        with patch('precedent_log.store.timestamp', return_value='2026-01-01T12:00:00Z'):
            Store('default').retire('P-1', 'Superseded policy.')
        root = self.home / 'precedent-log'
        before = {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in root.iterdir()}
        row = self.snapshot()['rows'][0]
        self.assertEqual(row['receipt'], {'author': 'desktop:session-example', 'surface': 'slash',
                         'at': '2026-01-01T10:00:00Z', 'source_task': ''})
        self.assertEqual(row['ruling'], 'Use staging.')
        self.assertEqual([item['kind'] for item in row['timeline']], ['saved', 'cite', 'explain', 'cite', 'retired'])
        self.assertEqual([item['task_id'] for item in row['timeline']], [None, 'card-1', 'card-2', 'card-1', None])
        self.assertEqual(row['timeline'][1]['detail'], 'block vetoed')
        self.assertEqual(row['timeline'][3]['detail'], 'completed')
        self.assertEqual(row['timeline'][-1]['detail'], 'Superseded policy.')
        self.assertEqual(row['timeline'][-1]['at'], '2026-01-01T12:00:00Z')
        self.assertEqual(row['timeline_total'], 5)
        self.assertEqual(row['cited_count'], 1)
        self.assertEqual(before, {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in root.iterdir()})

    def test_timeline_legacy_event_without_time(self):
        self.saved()
        events = Events('default')
        events.record('citation', 'old-card', ['P-1'])
        raw = json.loads(events.path.read_text())
        del raw['created_at']
        events.path.write_text(json.dumps(raw) + '\n')
        row = self.snapshot()['rows'][0]
        self.assertIsNone(row['timeline'][1]['at'])
        self.assertEqual(row['timeline'][1]['task_id'], 'old-card')

    def test_timeline_bounds_keep_lifecycle_and_show_omissions(self):
        self.saved()
        for n in range(MAX_TIMELINE_JOBS + 3):
            Events('default').record('relied', f'card-{n}', ['P-1'])
        Store('default').retire('P-1', 'Finished.')
        row = self.snapshot()['rows'][0]
        self.assertEqual(len(row['timeline']), MAX_TIMELINE_JOBS + 2)
        self.assertEqual(row['timeline_total'], MAX_TIMELINE_JOBS + 5)
        self.assertEqual(row['timeline'][0]['kind'], 'saved')
        self.assertEqual(row['timeline'][1]['task_id'], 'card-3')
        self.assertEqual(row['timeline'][-1]['kind'], 'retired')
        self.assertEqual(row['cited_count'], MAX_TIMELINE_JOBS + 3)

    def test_cli_receipt_uses_recorded_author_time_answer_and_source(self):
        import argparse
        import contextlib
        import io
        from precedent_log.commands import cli, setup_cli
        parser = argparse.ArgumentParser()
        setup_cli(parser)
        with patch('precedent_log.commands.getpass.getuser', return_value='operator'), \
                patch('precedent_log.store.timestamp', return_value='2026-01-01T10:00:00Z'), \
                contextlib.redirect_stdout(io.StringIO()):
            cli(parser.parse_args(['add', '--board', 'default', '--question', 'which environment?',
                                  '--ruling', 'Use staging.', '--source-task', 'source-card']))
        row = self.snapshot()['rows'][0]
        self.assertEqual(row['receipt'], {'author': 'operator', 'surface': 'cli',
                         'at': '2026-01-01T10:00:00Z', 'source_task': 'source-card'})
        self.assertEqual(row['ruling'], 'Use staging.')
        self.assertEqual(Store('default').list()[0]['author'], 'operator')

    def test_timeline_bad_job_time_and_torn_records_are_unavailable(self):
        self.saved()
        events = Events('default')
        events.record('justification', 'card-1', ['P-1'])
        event = json.loads(events.path.read_text())
        for bad in ({**event, 'task_id': 'bad card'}, {**event, 'created_at': 'invalid'},
                    {**event, 'created_at': '2999-01-01T00:00:00Z'}, {**event, 'veto': 'yes'}):
            events.path.write_text(json.dumps(bad) + '\n')
            self.assertEqual(self.snapshot()['state'], 'unavailable')
        events.path.write_text(json.dumps(event))
        self.assertEqual(self.snapshot()['state'], 'unavailable')

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
        self.assertEqual(len(row['title']), 100)

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

    def test_full_question_and_optional_files(self):
        question = 'which httpx version for the dependency upgrade in this project?'
        Store('default').add(question, 'Use the pinned version.')
        root = self.home / 'precedent-log'
        before = {p.name: p.read_bytes() for p in root.iterdir()}
        row = self.snapshot()['rows'][0]
        self.assertEqual(row['title'], question)
        self.assertEqual((row['cited_count'], row['veto_count'], row['last_veto'], row['cap_reached']), (0, 0, None, False))
        self.assertEqual(before, {p.name: p.read_bytes() for p in root.iterdir()})
        Events('default').record('veto', 'job', ['P-1'])
        self.assertEqual(self.snapshot()['last_veto']['title'], 'which httpx version for the dependency…')
        from precedent_log.store import Snapshot
        with patch.object(Store, '_read', return_value=Snapshot(entries={'P-1': {
                'id': 'P-1', 'question': 'x' * 3000, 'ruling': 'Use staging.'}})):
            self.assertEqual(len(self.snapshot()['rows'][0]['title']), 2000)

    def test_retire_slash_and_cli_grammar(self):
        import argparse
        import contextlib
        import io
        from precedent_log.commands import cli, setup_cli
        parser = argparse.ArgumentParser()
        setup_cli(parser)
        for n in (0, 1, 2):
            for surface in ('slash', 'cli'):
                row = self.saved()
                for j in range(n):
                    Events('default').record('relied', f'job-{j}', [row['id']])
                if surface == 'slash':
                    result = ruling(f"retire {row['id']} obsolete --board default")
                else:
                    output = io.StringIO()
                    with contextlib.redirect_stdout(output):
                        cli(parser.parse_args(['retire', row['id'], '--reason', 'obsolete', '--board', 'default']))
                    result = output.getvalue()
                self.assertIn(f"{n} completed {'job' if n == 1 else 'jobs'} cited it", result)

    def test_thousands_of_events_count_unique_jobs_and_keep_retired_timeline(self):
        self.saved()
        Store('default').retire('P-1', 'Finished.')
        events = Events('default')
        # Bulk-write real event schemas, avoiding quadratic writer recovery work.
        rows = [{'v': 1, 'board': 'default', 'event': kind, 'ids': ['P-1'],
                 'task_id': f'card-{n % 1000}', 'created_at': '2026-01-01T11:00:00Z'}
                for n in range(3000) for kind in ('relied', 'citation')]
        raw = ''.join(json.dumps(row, separators=(',', ':')) + '\n' for row in rows).encode()
        self.assertLess(len(raw), STORE_BYTES)
        events.path.write_bytes(raw)
        # Page reads must use bounded_read, never Events._read or Path.read_bytes.
        with patch.object(Events, '_read', side_effect=AssertionError('unbounded events read')), \
                patch('pathlib.Path.read_bytes', side_effect=AssertionError('unbounded file read')):
            row = self.snapshot()['rows'][0]
        self.assertEqual(row['cited_count'], 1000)
        self.assertEqual(len(row['jobs']), 20)
        self.assertEqual(row['timeline_total'], 6002)
        self.assertEqual(len(row['timeline']), 52)
        self.assertEqual(sum(item['kind'] == 'retired' for item in row['timeline']), 1)
        self.assertEqual(sum(item['kind'] == 'saved' for item in row['timeline']), 1)
        # One damaged line in a long history must never yield partial totals.
        events.path.write_bytes(raw + b'bad\n')
        self.assertEqual(self.snapshot()['state'], 'unavailable')
