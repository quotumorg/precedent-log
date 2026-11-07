"""First-run commands and executable recovery/review hints, without a provider."""
import support

import argparse
import contextlib
import io
import json
import shlex
import shutil
from unittest.mock import patch

from support import IsolatedTest, REPO
from precedent_log import commands
from precedent_log.stats import Events
from precedent_log.store import Store


class CliUxTests(IsolatedTest):
    def invoke(self, *args, exit_code=0):
        parser = argparse.ArgumentParser(prog='hermes precedent')
        commands.setup_cli(parser)
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            if exit_code:
                with self.assertRaises(SystemExit) as error:
                    commands.cli(parser.parse_args(args))
                self.assertEqual(error.exception.code, exit_code)
            else:
                self.assertEqual(commands.cli(parser.parse_args(args)), 0)
        return out.getvalue().strip(), err.getvalue().strip()

    def follow(self, message, marker, **kwargs):
        command = shlex.split(message.split(marker, 1)[1])
        self.assertEqual(command[:2], ['hermes', 'precedent'])
        return self.invoke(*command[2:], **kwargs)

    def test_empty_list_names_scope_and_keeps_json_contract(self):
        Store().add('default question', 'Default answer')
        out, err = self.invoke('list', '--board', 'trial')
        self.assertIn('board trial in this profile', out)
        self.assertIn('hermes precedent add --board trial', out)
        self.assertEqual(err, '')
        out, _ = self.invoke('list', '--board', 'trial', '--json')
        self.assertEqual(json.loads(out), [])
        self.assertEqual(len(Store().list()), 1)

    def test_unknown_lookup_hints_inspect_requested_board(self):
        Store().add('default question', 'Wrong-board answer')
        target = Store('trial')
        target.add('trial question', 'Trial answer')
        target.retire('P-1', 'old')
        before = target.path.read_bytes()
        for action in ('show', 'cited-by', 'retire'):
            extra = ['--reason', 'old'] if action == 'retire' else []
            with self.subTest(action=action):
                _, err = self.invoke(action, 'P-99', '--board', 'trial', *extra, exit_code=2)
                self.assertIn('board trial', err)
                out, _ = self.follow(err, 'run ')
                self.assertIn('P-1 [retired]: Trial answer', out)
                self.assertNotIn('Wrong-board answer', out)
                self.assertEqual(target.path.read_bytes(), before)

    def test_retire_hint_follows_cli_and_slash_board(self):
        Store().add('default question', 'Default answer')
        Events().record('relied', 't_default', ['P-1'])
        Store('trial').add('trial question', 'Trial answer')
        Events('trial').record('relied', 't_trial', ['P-1'])
        report, _ = self.invoke('retire', 'P-1', '--board', 'trial', '--reason', 'old')
        out, _ = self.follow(report, 'Review them: ')
        self.assertIn('t_trial | relied |', out)
        self.assertNotIn('t_default', out)
        with patch('precedent_log.store.resolve_board', return_value='trial'):
            Store('trial').add('next question', 'Next answer')
            report = commands.ruling('retire P-2 old')
        out, _ = self.follow(report, 'Review them: ')
        self.assertEqual(out, 'No citations.')

    def test_retire_hint_keeps_board_when_analytics_unavailable(self):
        Store('trial').add('trial question', 'Trial answer')
        with patch('precedent_log.commands.Events.cited_by', side_effect=OSError('unavailable')):
            report, _ = self.invoke('retire', 'P-1', '--board', 'trial', '--reason', 'old')
        self.assertIn('Cited-by log unavailable.', report)
        self.assertTrue(Store('trial').list(True)[0]['retired'])
        out, _ = self.follow(report, 'Review them: ')
        self.assertEqual(out, 'No citations.')

    def test_damaged_log_hints_verify_same_board_without_mutation(self):
        target = Store('trial')
        target.add('trial question', 'Trial answer')
        with target.path.open('ab') as stream:
            stream.write(b'broken\n')
        before = target.path.read_bytes()
        for args in [('list',), ('add', '--question', 'new question', '--ruling', 'new answer')]:
            with self.subTest(action=args[0]):
                _, err = self.invoke(*args, '--board', 'trial', exit_code=2)
                out, _ = self.invoke(*shlex.split(err[err.index('hermes precedent '):])[2:], exit_code=2)
                report = json.loads(out)
                self.assertEqual(report['board'], 'trial')
                self.assertFalse(report['ok'])
                self.assertEqual(report['issues'][0]['line'], 2)
                self.assertEqual(target.path.read_bytes(), before)
        self.assertEqual(target.read().active, [])

    def test_copied_plugin_quickstart_and_worker_prompt_without_tasks(self):
        destination = self.home / 'plugins/precedent-log'
        destination.mkdir(parents=True)
        for name in ('plugin.yaml', '__init__.py', 'LICENSE'):
            shutil.copy2(REPO / name, destination / name)
        shutil.copytree(REPO / 'precedent_log', destination / 'precedent_log')
        (self.home / 'config.yaml').write_text('plugins:\n  enabled: [precedent-log]\n  isolation: in_process\n')
        code = r'''
import json, os, subprocess, sys
from pathlib import Path

def cli(*args):
    offline = "import sys, runpy\ndef audit(event, args):\n    if event in {'socket.connect', 'socket.bind', 'socket.getaddrinfo'}: raise RuntimeError('Network disabled')\nsys.addaudithook(audit)\nrunpy.run_module('hermes_cli.main', run_name='__main__')\n"
    p = subprocess.run([sys.executable, '-B', '-c', offline, 'precedent', *args],
                       capture_output=True, text=True, timeout=30)
    assert p.returncode == 0, p.stdout + p.stderr
    return p.stdout.strip()

rid = cli('add', '--board', 'default', '--question', 'staging or prod DB for the schema migration?',
          '--ruling', 'Use staging for the local plan. Production needs fresh approval.', '--keys', 'staging,prod')
assert rid == 'P-1', rid
assert 'P-1: Use staging for the local plan.' in cli('list', '--board', 'default')
row = json.loads(cli('show', rid, '--board', 'default'))
assert row['board'] == 'default' and row['retired'] is False
from hermes_cli import plugins
assert plugins.render_system_prompt_sections({'session_id': 'trial'}) == []
os.environ['HERMES_KANBAN_TASK'] = 't_trial'
sections = plugins.render_system_prompt_sections({'session_id': 'trial'})
assert any(section.id == 'precedent-log.board' and row['ruling'] in section.content for section in sections)
assert not list(Path(os.environ['HERMES_HOME']).rglob('kanban.db'))
print('Copied plugin: add/list/show and worker prompt registration pass without a task or provider.')
'''
        result = self.process(code)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
