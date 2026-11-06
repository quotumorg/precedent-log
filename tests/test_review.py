"""r1 counterexamples adapted to r2. Real core transitions are in test_core.py."""

import support

import argparse
import contextlib
import io
import json
import os
from pathlib import Path
import shlex
from unittest.mock import patch

from support import IsolatedTest
from precedent_log import commands, guard, section
from precedent_log.gate import pre_tool_call
from precedent_log.match import match
from precedent_log.policy import Policy
from precedent_log.stats import Events
from precedent_log.store import Store, canonical, digest, call_board


CORPUS = json.loads(Path(__file__).with_name('matching-corpus.json').read_text())


class ReviewTests(IsolatedTest):
    def setUp(self):
        super().setUp()
        self.store = Store()
        self.store.add(CORPUS['question'], CORPUS['ruling'], CORPUS['keys'])
        self.reason = CORPUS['question']

    def gate(self, reason=None, task='t_review', **args):
        return pre_tool_call('kanban_block', {'kind': 'needs_input', 'reason': reason or self.reason, **args}, task_id=task)

    def forged(self):
        state = self.store.read()
        row = dict(state.entries['P-1'])
        row.update(id='P-2', question='forged worker policy', ruling='Worker made this ruling', keys=[], prev=state.tail)
        row.pop('retired')
        row['h'] = digest(row)
        return canonical(row)

    def test_terminal_workdir_refuses_valid_worker_append(self):
        args = {'command': "printf '%s\\n' " + shlex.quote(self.forged()) + ' >> default.jsonl',
                'workdir': str(self.store.directory)}
        before = self.store.path.read_bytes()
        with patch.dict(os.environ, {'HERMES_KANBAN_TASK': 't_review'}):
            self.assertEqual(guard.check('terminal', args)['action'], 'block')
        self.assertEqual(self.store.path.read_bytes(), before)
        self.assertTrue(self.store.verify()['ok'])

    def test_script_indirection_and_marked_store_add_refused(self):
        payload = self.home / 'payload.py'
        content = "from precedent_log.store import Store\nStore().add('worker invented policy', 'Invented answer')\n"
        with patch.dict(os.environ, {'HERMES_KANBAN_TASK': 't_review'}):
            self.assertIsNone(guard.check('write_file', {'path': str(payload), 'content': content}))
            payload.write_text(content)
            self.assertEqual(guard.check('execute_code', {'code': 'import runpy; runpy.run_path("payload.py")'}, str(self.home))['action'], 'block')
            with self.assertRaises(PermissionError):
                self.store.add('worker policy', 'forged')
        for marker in ('HERMES_KANBAN_TASK', 'HERMES_DELEGATED_CHILD_CONTEXT'):
            result = self.process('import runpy; runpy.run_path(' + repr(str(payload)) + ')', **{marker: '1'})
            self.assertNotEqual(result.returncode, 0)
            self.assertIn(guard.REFUSAL, result.stderr)
        self.assertEqual(len(self.store.list()), 1)

    def test_process_stdin_writer_refused_without_literal_store_path(self):
        with patch.dict(os.environ, {'HERMES_KANBAN_TASK': 't_review'}):
            self.assertEqual(guard.check('terminal', {'command': 'tee -a default.jsonl', 'workdir': str(self.store.directory), 'background': True})['action'], 'block')
            for action in ('write', 'submit'):
                self.assertEqual(guard.check('process_manage', {'action': action, 'session_id': 'owned', 'data': self.forged()})['action'], 'block')
            self.assertIsNone(guard.check('process_manage', {'action': 'poll', 'session_id': 'owned'}))

    def test_terminal_symlink_alias_cannot_replace_log(self):
        (self.home / 'rules').symlink_to(self.store.directory, target_is_directory=True)
        with patch.dict(os.environ, {'HERMES_KANBAN_TASK': 't_review'}):
            for command in ('cp replacement.jsonl rules/default.jsonl', 'cat replacement.jsonl>rules/default.jsonl',
                            'tee --output=rules/default.jsonl'):
                args = {'command': command, 'workdir': str(self.home)}
                self.assertEqual(guard.check('terminal', args)['action'], 'block')
            self.assertEqual(guard.check('terminal', {'command': 'touch default.jsonl', 'workdir': str(self.home / 'rules')})['action'], 'block')

    def test_env_clearing_global_board_option_and_repair_guarded(self):
        with patch.dict(os.environ, {'HERMES_KANBAN_TASK': 't_review', 'HERMES_DELEGATED_CHILD_CONTEXT': '1'}):
            for action in ('add --question forged --ruling forged', 'retire P-1 --reason old', 'repair --truncate-after 0'):
                command = 'env -u HERMES_KANBAN_TASK -u HERMES_DELEGATED_CHILD_CONTEXT hermes precedent --board default ' + action
                self.assertEqual(guard.check('terminal', {'command': command})['action'], 'block')
                parser = argparse.ArgumentParser()
                commands.setup_cli(parser)
                with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
                    commands.cli(parser.parse_args(['--board', 'default', *shlex.split(action)]))
                self.assertEqual(error.exception.code, 2)
            with self.assertRaises(PermissionError):
                self.store.repair(0)

    def test_unmarked_same_user_is_outside_boundary_and_ordinary_edits_detected(self):
        self.assertFalse(guard.is_worker_or_child())
        self.assertEqual(commands.ruling('add human policy => Human answer'), 'Added P-2')
        self.store.path.write_text(self.store.path.read_text().replace('Human answer', 'Manual answer'))
        self.assertFalse(self.store.verify()['ok'])
        # No external anchor: a fully recomputed chain remains forgeable by the OS user.

    def test_retired_unrelated_unknown_and_gibberish_citations_vetoed(self):
        self.store.add('vendor contract approval', 'Ask purchasing')
        self.store.retire('P-2', 'Revoked')
        self.store.add('unrelated purchasing issue', 'Ask purchasing')
        for n, suffix in enumerate(('per precedent P-2', 'no precedent applies: ........',
                                    'per precedent P-999', 'per precedent P-3')):
            result = self.gate(self.reason + ' ' + suffix, task=f't_bad_{n}')
            self.assertEqual(result['action'], 'block')
        for n, rid in enumerate(('P-2', 'P-999', 'P-0', 'P-01')):
            self.assertIn(rid + ' is not an active ruling on this board', self.gate('per precedent ' + rid, task=f'unknown{n}')['message'])
        self.assertEqual(Events().summary()['passes_with_citation'], 0)

    def test_two_vetoes_then_visible_warning_not_endless_loop(self):
        outcomes = [self.gate() for _ in range(3)]
        self.assertEqual([r['action'] for r in outcomes], ['block', 'block', 'modify'])
        self.assertIn('[precedent-log] escalated without citing candidates P-1', outcomes[-1]['args']['reason'])

    def test_foreign_only_id_is_explicitly_invalid_even_unmatched(self):
        other = Store('release')
        other.add('foreign first policy', 'Foreign answer')
        other.add('foreign second policy', 'Foreign answer')
        for n, reason in enumerate((self.reason + ' per precedent P-2', 'per precedent P-2 on release')):
            self.assertIn('P-2 is not an active ruling on this board', self.gate(reason, task=f'foreign{n}')['message'])

    def test_ten_new_questions_are_candidates_not_orders(self):
        for n, case in enumerate(CORPUS['cases'][:10]):
            reason, task = case['reason'], f'new{n}'
            self.assertEqual([r['id'] for r in match(reason, self.store.list())], case['r2_matches'])
            result = self.gate(reason, task=task)
            self.assertIn('candidate rulings', result['message'])
            self.assertIn('Decide whether this is the same question', result['message'])
            explanation = 'no precedent applies: P-1 decides the database target, this asks a separate approval question.'
            result = self.gate(reason + ' ' + explanation, task=task)
            self.assertEqual(result['action'], 'modify')
            self.assertIn('syntactic explanation marker', result['args']['reason'])

    def test_four_missed_rephrasings_match_human_aliases(self):
        row = self.store.list()[0]
        for case in CORPUS['cases'][10:]:
            self.assertEqual(match(case['reason'], [row]), [])
        self.store.retire('P-1', 'Add reviewed aliases')
        added = self.store.add(CORPUS['question'], CORPUS['ruling'], CORPUS['keys'], also=CORPUS['also'])
        for n, case in enumerate(CORPUS['cases'][10:]):
            self.assertEqual([r['id'] for r in match(case['reason'], self.store.list())], [added['id']])
            self.assertEqual(self.gate(case['reason'], task=f'alias{n}')['action'], 'block')

    def test_quarantine_and_repair_never_resurrect_retirement(self):
        self.store.add('unrelated vendor contract', 'Use approved vendor')
        self.store.retire('P-1', 'Policy revoked; never use staging now')
        original = self.store.path.read_text().replace('approved vendor', 'alternate vendor')
        self.store.path.write_text(original)
        self.assertFalse(self.store.verify()['ok'])
        self.assertEqual(self.store.read().active, [])
        result = self.gate()
        self.assertIn('log damaged at line 2, rulings not applied; run hermes precedent verify', result['args']['reason'])
        with patch.dict(os.environ, {'HERMES_KANBAN_TASK': 't_review'}):
            self.assertIn('log damaged at line 2', section.render())
        for action in (lambda: self.store.add('x', 'y'), lambda: self.store.retire('P-1', 'old'), lambda: self.store.repair(2)):
            with self.assertRaises(ValueError):
                action()
        report = self.store.repair(1)
        self.assertEqual(Path(report['backup']).read_text(), original)
        self.assertTrue(self.store.verify()['ok'])
        self.assertEqual(self.store.list(), [])
        self.assertTrue(self.store.list(True)[0]['retired'])
        self.assertEqual(self.store.add('different policy', 'New ruling')['id'], 'P-3')
        self.store.repair(0)
        self.assertEqual(self.store.add('later policy', 'Later answer')['id'], 'P-4')

    def test_partial_event_tail_recovers_and_retains_veto_counts(self):
        self.assertEqual(self.gate()['action'], 'block')
        with Events().path.open('a') as stream:
            stream.write('{"v":')
        result = self.gate()
        self.assertEqual(result['action'], 'block')
        self.assertIn('candidate rulings', result['message'])
        self.assertEqual((self.store.directory / 'default.events.torn').read_text(), '{"v":\n')
        self.assertEqual(Events().summary()['invalid_event_lines'], 0)
        self.assertEqual(Events().summary()['gated_vetoes'], 2)
        code = "import json; from precedent_log.gate import pre_tool_call; print(json.dumps(pre_tool_call('kanban_block', {'reason': 'staging prod migrations'}, task_id='t_review')))"
        result = self.process(code)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('escalated without citing candidates P-1', json.loads(result.stdout)['args']['reason'])

    def test_profile_override_and_respawn_counts(self):
        from hermes_constants import set_hermes_home_override, reset_hermes_home_override
        profile = self.home / 'profiles/other'
        token = set_hermes_home_override(profile)
        try:
            self.assertEqual(Store().directory, profile / 'precedent-log')
            self.assertEqual(Store().list(), [])
        finally:
            reset_hermes_home_override(token)
        with patch.dict(os.environ, {'HERMES_KANBAN_TASK': 't_persistent'}):
            self.assertEqual(self.gate()['action'], 'block')
            self.assertEqual(self.gate()['action'], 'block')
        result = self.process("import json; from precedent_log.gate import pre_tool_call; print(json.dumps(pre_tool_call('kanban_block', {'reason': 'staging prod migrations'})))", HERMES_KANBAN_TASK='t_persistent')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['action'], 'modify')

    def test_explanation_names_all_previously_shown_candidates(self):
        self.store.add(self.reason, 'Second candidate')
        self.store.add(self.reason, 'Third candidate')
        self.assertEqual(self.gate()['action'], 'block')
        result = self.gate('no precedent applies: P-1 concerns something different from this task.')
        self.assertEqual(result['action'], 'block')
        self.assertIn('P-2', result['message'])
        result = self.gate('no precedent applies: P-1 P-2 P-3 concern target selection; this is a new approval question.')
        self.assertIn('syntactic explanation marker', result['args']['reason'])

    def test_analytics_failures_annotated_on_every_policy_branch(self):
        with patch.object(Events, 'record', side_effect=OSError('unavailable')):
            self.assertIn('events unavailable', self.gate()['message'])
            self.assertIn('events unavailable', self.gate(self.reason + ' per precedent P-1')['args']['reason'])
            self.assertIn('events unavailable', self.gate('no precedent applies: P-1 decides targets, this asks who owns rollback.')['args']['reason'])
            self.assertIn('events unavailable', self.gate('new vendor question', task='unmatched')['args']['reason'])
            self.assertEqual(self.gate()['action'], 'block')
            self.assertIn('escalated without citing candidates P-1', self.gate()['args']['reason'])
        # Policy survives respawn even if no analytic event was recorded.
        result = self.process("import json; from precedent_log.gate import pre_tool_call; print(json.dumps(pre_tool_call('kanban_block', {'reason':'staging prod migrations'}, task_id='t_review')))" )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['action'], 'modify')

    def test_policy_storage_failure_stays_bounded_and_visible_in_process(self):
        with patch.object(Policy, '_save', side_effect=OSError('unavailable')):
            outcomes = [self.gate() for _ in range(3)]
        self.assertEqual([r['action'] for r in outcomes], ['block', 'block', 'modify'])
        for result in outcomes:
            self.assertIn('policy storage unavailable', result.get('message', '') + result.get('args', {}).get('reason', ''))

    def test_alias_cli_and_whole_normalized_keys(self):
        for key in ('prod db', 'prod-db', 'the', ' prod/db '):
            with self.assertRaises(ValueError):
                self.store.add('target policy', 'Answer', [key])
        parser = argparse.ArgumentParser()
        commands.setup_cli(parser)
        with contextlib.redirect_stdout(io.StringIO()):
            commands.cli(parser.parse_args(['add', '--question', 'target policy', '--ruling', 'Answer', '--keys', 'production', '--also', 'test schema database', '--also', 'preprod upgrade environment']))
        row = self.store.list()[0]
        self.assertEqual(row['also'], ['test schema database', 'preprod upgrade environment'])
        self.assertEqual(match('productional', [row]), [])
        self.assertEqual(match('production', [row]), [row])
