import support

import argparse
import contextlib
import io
import os
from unittest.mock import patch

from support import IsolatedTest
from precedent_log import commands
from precedent_log.guard import REFUSAL, check
from precedent_log.section import render
from precedent_log.store import Store


class GuardCommandTests(IsolatedTest):
    def parse(self, *args):
        parser = argparse.ArgumentParser()
        commands.setup_cli(parser)
        return parser.parse_args(args)

    def test_cli_and_slash_refuse_worker_and_descendant_mutations(self):
        Store().add("staging prod migrations", "Use staging")
        for marker in ("HERMES_KANBAN_TASK", "HERMES_DELEGATED_CHILD_CONTEXT"):
            with self.subTest(marker=marker), patch.dict(os.environ, {marker: "t_worker"}):
                for args in (self.parse("add", "--question", "question", "--ruling", "answer"),
                             self.parse("retire", "P-1", "--reason", "old")):
                    with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
                        commands.cli(args)
                    self.assertEqual(error.exception.code, 2)
                self.assertEqual(commands.ruling("add question => answer"), REFUSAL)
                self.assertEqual(commands.ruling("retire P-1 old"), REFUSAL)
                self.assertIn("P-1", commands.rulings())
        self.assertEqual(len(Store().list()), 1)

    def test_real_in_process_delegated_child(self):
        from agent.delegation_context import delegated_child_context
        with delegated_child_context():
            self.assertEqual(commands.ruling("add question => answer"), REFUSAL)
            self.assertEqual(check("write_file", {"path": str(self.home / "precedent-log/default.jsonl")})["message"], REFUSAL)
            self.assertEqual(render(), "")

    def test_guard_paths_traversal_symlinks_and_v4a(self):
        directory = self.home / "precedent-log"
        directory.mkdir()
        work = self.home / "work"
        work.mkdir()
        (work / "alias").symlink_to(directory, target_is_directory=True)
        targets = (str(directory / "default.jsonl"), "../precedent-log/default.jsonl", "alias/default.jsonl")
        with patch.dict(os.environ, {"HERMES_KANBAN_TASK": "t_worker"}):
            for tool in ("write_file", "patch"):
                for path in targets:
                    self.assertEqual(check(tool, {"path": path}, str(work))["message"], REFUSAL)
            for marker in ("Add File", "Update File", "Delete File"):
                patch_text = f"*** Begin Patch\n*** {marker}: alias/default.jsonl\n+x\n*** End Patch"
                self.assertEqual(check("patch", {"mode": "patch", "patch": patch_text}, str(work))["message"], REFUSAL)
            self.assertEqual(check("patch", {"mode": "patch", "patch": "*** Move File: a -> alias/default.jsonl"}, str(work))["message"], REFUSAL)
            self.assertEqual(check("patch", {"mode": "patch", "patch": "***Move File:a->alias/default.jsonl"}, str(work))["message"], REFUSAL)
            self.assertEqual(check("text_to_speech", {"output_path": "alias/default.jsonl"}, str(work))["message"], REFUSAL)
            self.assertIsNone(check("write_file", {"path": str(self.home / "precedent-log-other/file")}, str(work)))
        self.assertIsNone(check("write_file", {"path": targets[0]}))

    def test_guard_terminal_process_and_code(self):
        with patch.dict(os.environ, {"HERMES_DELEGATED_CHILD_CONTEXT": "1"}):
            for text in (f"cat {self.home}/precedent-log/default.jsonl", "echo x > precedent-log/a",
                         "hermes precedent add --question q --ruling r", "hermes precedent retire P-1 --reason old"):
                for tool, key in (("terminal", "command"), ("process_manage", "data"), ("execute_code", "code")):
                    self.assertEqual(check(tool, {key: text})["message"], REFUSAL)
            self.assertIsNone(check("terminal", {"command": "hermes precedent list"}))
        self.assertIsNone(check("terminal", {"command": "hermes precedent add --question q --ruling r"}))

    def test_human_commands_and_provenance(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            commands.cli(self.parse("add", "--question", "staging prod?", "--ruling", "Use staging", "--keys", "staging,prod", "--from-task", "t_source"))
        self.assertEqual(output.getvalue().strip(), "P-1")
        self.assertEqual(Store().list()[0]["source_task"], "t_source")
        self.assertEqual(commands.ruling("add vendor approval => Ask owner [keys: vendor, approval]", platform="telegram", session_key="s123"), "Added P-2")
        row = Store().list()[0]
        self.assertEqual((row["author"], row["surface"], row["keys"]), ("telegram:s123", "slash", ["vendor", "approval"]))
        self.assertEqual(commands.ruling("retire P-2 Replaced"),
                         'P-2 retired. 0 completed jobs cited it: (none). Review them: hermes precedent cited-by P-2')
        for args in (self.parse("list", "--all", "--json"), self.parse("show", "P-2"), self.parse("verify"), self.parse("stats")):
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(commands.cli(args), 0)
        self.assertEqual(self.parse("--board", "one", "list").board, "one")
        self.assertEqual(self.parse("list", "--board", "two").board, "two")

    def test_section_cap_char_budget_and_truncation(self):
        store = Store()
        for n in range(24):
            store.add(f"question {n}", f"ruling {n}")
        self.assertEqual(render(), "")
        with patch.dict(os.environ, {"HERMES_KANBAN_TASK": "t_worker"}):
            result = render()
            self.assertEqual(sum(line.startswith('<ruling-data id="P-') for line in result.splitlines()), 20)
            self.assertIn("4 rulings omitted: 0 exceed remaining character budget; 4 exceed 20-row limit", result)
            self.assertLess(result.index('id="P-24"'), result.index('id="P-23"'))
            for cap in (0, 20, 50, 130, 250, 4000):
                limited = render(max_chars=cap)
                self.assertLessEqual(len(limited), cap)
                if limited:
                    self.assertIn("rulings omitted:", limited)
        store.retire("P-24", "Old")
        with patch.dict(os.environ, {"HERMES_KANBAN_TASK": "t_worker"}):
            self.assertNotIn('id="P-24"', render())

    def test_section_shows_ids_question_ruling_but_not_match_metadata(self):
        store = Store()
        store.add("Which\n environment?", "Use\t staging.", keys=["privatekey"],
                  also=["privatealias"], source_task="t_private", author="privateauthor")
        with patch.dict(os.environ, {"HERMES_KANBAN_TASK": "t_worker"}):
            result = render()
            self.assertIn('id="P-1"', result)
            self.assertIn(r'ruling: "Use\t staging."', result)
            self.assertIn(r'question: "Which\n environment?"', result)
            for private in ("privatekey", "privatealias", "t_private", "privateauthor"):
                self.assertNotIn(private, result)
        store.retire("P-1", "Replaced")
        with patch.dict(os.environ, {"HERMES_KANBAN_TASK": "t_worker"}):
            self.assertEqual(render(), "")

    def test_section_many_long_rulings_stays_within_default_budget(self):
        store = Store()
        for number in range(30):
            store.add(f"question {number} " + "q" * 100, "r" * 600)
        with patch.dict(os.environ, {"HERMES_KANBAN_TASK": "t_worker"}):
            result = render()
        self.assertLessEqual(len(result), 4000)
        rows = [line for line in result.splitlines() if line.startswith('<ruling-data id="P-')]
        self.assertGreater(len(rows), 0)
        self.assertLess(len(rows), 20)
        self.assertTrue(rows[0].startswith('<ruling-data id="P-30"'))
        self.assertIn(f"{30 - len(rows)} rulings omitted:", result)
