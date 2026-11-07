import support

import contextlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
from unittest.mock import Mock, patch

from support import IsolatedTest, LAB_SOURCE, REPO
from demo.run import Harness, citation_evidence, outside_git, parse_args


def exchange(name, args, result, call_id="call"):
    return [{"role": "assistant", "tool_calls": [
        {"id": call_id, "function": {"name": name, "arguments": json.dumps(args)}}]},
        {"role": "tool", "tool_call_id": call_id, "content": json.dumps(result)}]


def attempt(messages):
    return {"task_id": "t_example", "worker": {"result": {"messages": messages}}}


def completion(summary="per precedent P-1", ok=True):
    return exchange("kanban_complete", {"summary": summary}, {"ok": ok})


VETO = exchange("kanban_block", {}, {"error": "[precedent-log] candidate rulings. P-1: Use staging."})


class DemoObservationTests(IsolatedTest):
    def test_citation_accepts_real_wording_and_fake_phrase(self):
        for summary, output in (
                ("answered by precedent P-1: use staging", "Precedent cited: P-1"),
                ("per precedent P-1", "per precedent P-1"),
                ("(p-1): staging", "**p-1**")):
            with self.subTest(summary=summary):
                evidence = citation_evidence([attempt(completion(summary))], output)
                self.assertTrue(evidence["citation_found"])
                self.assertEqual(evidence["citation_path"], "prompt")

    def test_citation_needs_both_summary_and_output_with_word_boundaries(self):
        for invalid in (None, "", "P-10", "XP-1", "P-1a", "_P-1", "P-1_"):
            for summary, output in ((invalid, "P-1"), ("P-1", invalid)):
                with self.subTest(summary=summary, output=output):
                    evidence = citation_evidence([attempt(completion(summary))], output)
                    self.assertFalse(evidence["citation_found"])
                    self.assertIsNone(evidence["citation_path"])

    def test_block_rejection_final_text_and_failed_completion_are_not_citations(self):
        for messages in (
                exchange("kanban_block", {"reason": "no precedent applies: P-1"}, {"ok": True}),
                [{"role": "assistant", "content": "Completed per precedent P-1"}],
                completion(ok=False), completion()[:1]):
            with self.subTest(messages=messages):
                self.assertFalse(citation_evidence([attempt(messages)], "P-1")["citation_found"])

    def test_veto_path_requires_matching_tool_result_before_completion(self):
        self.assertEqual(citation_evidence([attempt(VETO + completion())], "P-1")["citation_path"], "veto")
        self.assertEqual(citation_evidence([attempt(VETO), attempt(completion())], "P-1")["citation_path"], "veto")
        self.assertEqual(citation_evidence([attempt(completion() + VETO)], "P-1")["citation_path"], "prompt")
        unrelated = exchange("read_file", {}, {"error": "[precedent-log] candidate rulings."})
        self.assertEqual(citation_evidence([attempt(unrelated + completion())], "P-1")["citation_path"], "prompt")
        wrong_id = [VETO[0], {**VETO[1], "tool_call_id": "other"}]
        self.assertIsNone(citation_evidence([attempt(wrong_id + completion())], "P-1")["citation_path"])

    def test_successful_block_is_not_a_veto_or_prompt_path(self):
        blocked = exchange("kanban_block", {}, {"ok": True, "status": "blocked"})
        evidence = citation_evidence([attempt(blocked), attempt(completion())], "P-1")
        self.assertTrue(evidence["citation_found"])
        self.assertIsNone(evidence["citation_path"])

    def test_completion_for_another_task_does_not_count(self):
        other = exchange("kanban_complete", {"task_id": "t_other", "summary": "P-1"}, {"ok": True})
        self.assertFalse(citation_evidence([attempt(other)], "P-1")["citation_found"])

    def test_git_parent_walk_handles_directory_file_and_symlink(self):
        for marker in ("directory", "file"):
            root = self.home / marker
            root.mkdir()
            if marker == "directory":
                (root / ".git").mkdir()
            else:
                (root / ".git").write_text("gitdir: /unused/worktree\n")
            link = self.home / (marker + "-link")
            link.symlink_to(root, target_is_directory=True)
            for path in (root, root / "not/created/yet", link / "nested"):
                with self.subTest(path=path), self.assertRaisesRegex(ValueError, "outside any git work tree"):
                    outside_git(path, "Run directory")
        clean = self.home / "uncreated/run"
        self.assertEqual(outside_git(clean, "Run directory"), clean.resolve())
        self.assertFalse(clean.exists())

    def test_cli_rejects_repo_home_or_output_before_creating_anything(self):
        for target in ("--hermes-home", "--out", "HERMES_HOME"):
            root = self.home / target.replace("-", "")
            root.mkdir()
            (root / ".git").write_text("gitdir: /unused/worktree\n")
            home, output = self.home / "new-home", self.home / "new-out"
            env = {"PATH": os.environ.get("PATH", ""), "PYTHONDONTWRITEBYTECODE": "1"}
            command = [sys.executable, "-B", str(REPO / "demo/run.py"), "--hermes-source", str(LAB_SOURCE)]
            if target == "HERMES_HOME":
                env["HERMES_HOME"] = str(root / "home")
            else:
                command += ["--hermes-home", str(root / "home" if target == "--hermes-home" else home)]
            command += ["--out", str(root / "out" if target == "--out" else output)]
            result = subprocess.run(command, cwd=self.home, env=env, capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn("outside any git work tree", result.stderr)
            self.assertIn("Hermes home" if target != "--out" else "Run directory", result.stderr)
            self.assertEqual(list(root.iterdir()), [root / ".git"])
            self.assertFalse(home.exists())
            self.assertFalse(output.exists())

    def test_default_output_is_outside_repo(self):
        with patch.object(sys, "argv", ["demo/run.py", "--hermes-source", str(LAB_SOURCE)]):
            args = parse_args()
        self.assertFalse(args.out.resolve().is_relative_to(REPO))
        outside_git(args.out, "Run directory")

    def test_veto_argument_default_choices_and_invalid_value(self):
        base = ["demo/run.py", "--hermes-source", str(LAB_SOURCE)]
        for argv, mode in ((base, "enforce"), (base + ["--veto", "enforce"], "enforce"),
                           (base + ["--veto", "advisory"], "advisory")):
            with patch.object(sys, "argv", argv):
                self.assertEqual(parse_args().veto, mode)
        with patch.object(sys, "argv", base + ["--veto", "typo"]), \
                contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
            parse_args()
        self.assertEqual(error.exception.code, 2)

    def test_veto_mode_reaches_config_transcript_and_result_lines_offline(self):
        for mode in ("enforce", "advisory"):
            with self.subTest(mode=mode):
                result = self.process('''
import contextlib, io, json, sys
from pathlib import Path
from unittest.mock import Mock
from demo.run import Harness, parse_args
sys.argv = ['demo/run.py', '--hermes-source', SOURCE, '--hermes-home', HOME + '/lab-' + MODE,
            '--out', HOME + '/runs', '--run-id', MODE, '--veto', MODE]
h = Harness(parse_args())
h.command = Mock()
h.warm_up = Mock(side_effect=RuntimeError('stop before worker'))
try:
    h.execute(None)
except RuntimeError as exc:
    assert str(exc) == 'stop before worker'
config = json.loads((h.home / 'config.yaml').read_text())
assert config['plugins']['entries']['precedent-log']['settings']['precedent_log']['veto'] == MODE
assert config['plugins']['enabled'] == ['precedent-log']
assert json.loads((h.out / 'transcript.json').read_text())['veto'] == MODE
h.tasks['T2'] = {'id': 't_example', 'workspace': str(h.out), 'output': 'missing.md'}
h.command = Mock(return_value=Mock(stdout=json.dumps({
    'task': {'workspace_path': str(h.out), 'status': 'blocked', 'block_reason': 'staging prod'},
    'events': [{'kind': 'blocked', 'payload': {'kind': 'needs_input'}}]})))
output = io.StringIO()
with contextlib.redirect_stdout(output):
    h.snapshot('T2', 'attempt-1')
assert 'mode=' + MODE in output.getvalue(), output.getvalue()
'''.replace('SOURCE', repr(str(LAB_SOURCE))).replace('HOME', repr(str(self.home))).replace('MODE', repr(mode)))
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def warmup_harness(self):
        harness = Harness.__new__(Harness)
        harness.out = self.home
        (self.home / "attempts").mkdir()
        harness.args = SimpleNamespace(warmup_timeout=1)
        harness.provider, harness.base_url = "custom", "http://127.0.0.1"
        harness.data = {"model": "fake-model", "warmups": []}
        harness.env, harness.save = {}, Mock()
        return harness

    def test_advisory_records_prompt_completion_or_allowed_reask(self):
        for mode, second_state, citation, expected_failure in (
                ("advisory", "blocked", False, None), ("advisory", "done", True, None),
                ("advisory", "done", False, "missing P-1 citation"),
                ("advisory", "running", False, "expected done"),
                ("enforce", "blocked", False, "expected done")):
            with self.subTest(mode=mode, state=second_state, citation=citation):
                h = Harness.__new__(Harness)
                h.board = "precedent-demo"
                h.home = self.home / f"lab-{mode}-{second_state}-{citation}"
                h.home.mkdir()
                h.args = SimpleNamespace(model_provider="fake", no_plugin=False, veto=mode,
                                         repo=REPO, include_b2=False)
                h.fixture = json.loads((REPO / "demo/tasks.json").read_text())
                h.server = None
                h.data = {"model": "fake-model", "failures": [], "cards": {
                    label: {"state": second_state if label == "T2" else state,
                            "block_kind": "needs_input", "output_present":
                                (second_state == "done" if label == "T2" else state == "done"),
                            "citation_found": citation, "last_reason_or_summary": "staging prod"}
                    for label, state in (("T1", "done"), ("T2", "done"), ("T3", "blocked"), ("T4", "blocked"))}}
                h.tasks = {"T1": {"id": "t_first"}}
                h.command = Mock(return_value=Mock(returncode=0, stdout="recorded"))
                h.warm_up = h.create = h.snapshot = h.save = Mock()
                h.run_task = Mock(return_value={"state": "blocked", "block_kind": "needs_input", "output_present": False})
                with contextlib.redirect_stdout(io.StringIO()):
                    h.execute(None)
                if expected_failure:
                    self.assertTrue(any(expected_failure in f for f in h.data["failures"]), h.data["failures"])
                else:
                    self.assertEqual(h.data["failures"], [])
                self.assertTrue(h.data["finished"])

    def test_warmup_retains_failed_start_then_retries_in_new_process(self):
        harness = self.warmup_harness()
        def start(argv, **kwargs):
            spec = json.loads(Path(argv[-1]).read_text())
            number = len(harness.data["warmups"])
            Path(spec["result_file"]).write_text(json.dumps({"initialized": number == 2}))
            return Mock(pid=100 + number, returncode=1 if number == 1 else 0,
                        communicate=Mock(return_value=("restart required" if number == 1 else "ready", "")))
        with patch("demo.run.subprocess.Popen", side_effect=start), contextlib.redirect_stdout(io.StringIO()):
            harness.warm_up()
        self.assertEqual([r["returncode"] for r in harness.data["warmups"]], [1, 0])
        self.assertIn("restart required", harness.data["warmups"][0]["stdout"])
        self.assertNotEqual(*[r["pid"] for r in harness.data["warmups"]])
        self.assertGreaterEqual(harness.save.call_count, 6)

    def test_warmup_timeout_records_failure_and_aborts_before_t1(self):
        harness = self.warmup_harness()
        process = Mock(pid=123, returncode=-9)
        process.communicate.side_effect = [subprocess.TimeoutExpired("warmup", 1), ("cold start", "")] * 2
        with patch("demo.run.subprocess.Popen", return_value=process), patch("demo.run.os.killpg") as kill, \
                contextlib.redirect_stdout(io.StringIO()), self.assertRaisesRegex(RuntimeError, "T1 was not created"):
            harness.warm_up()
        self.assertEqual(kill.call_count, 2)
        self.assertEqual(len(harness.data["warmups"]), 2)
        self.assertTrue(all(r["error"] == "TimeoutExpired" for r in harness.data["warmups"]))
        self.assertTrue(all(r["stdout"] == "cold start" for r in harness.data["warmups"]))
