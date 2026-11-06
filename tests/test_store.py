import support

import json
import hashlib
import os
from pathlib import Path
import subprocess
import sys
import time
from unittest.mock import patch

from support import IsolatedTest, LAB_SOURCE, REPO, OFFLINE
from precedent_log.store import Store, canonical, digest, locked, resolve_board
from precedent_log.match import match
from precedent_log.section import render


class StoreTests(IsolatedTest):
    def test_add_retire_restart_and_audit(self):
        store = Store()
        self.assertEqual(store.add("staging prod database", "Use staging")["id"], "P-1")
        store.retire("P-1", "Replaced")
        fresh = Store()
        self.assertEqual(fresh.add("staging prod database", "Ask the owner")["id"], "P-2")
        self.assertEqual([row["id"] for row in fresh.list()], ["P-2"])
        self.assertTrue(fresh.list(True)[1]["retired"])
        self.assertEqual([row["id"] for row in match("staging prod database", fresh.list(True))], ["P-2"])
        with patch.dict(os.environ, {"HERMES_KANBAN_TASK": "t_worker"}):
            self.assertNotIn("P-1:", render())
        result = self.process("from precedent_log.store import Store; print(Store().add('another question', 'Another answer')['id'])")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "P-3")
        self.assertTrue(fresh.verify()["ok"])

    def test_edited_and_deleted_middle_line_number(self):
        store = Store()
        for n in range(4):
            store.add("staging prod database", f"Answer {n}")
        original = store.path.read_text().splitlines()
        altered = json.loads(original[1])
        altered["ruling"] = "Malicious answer"
        store.path.write_text("\n".join([original[0], canonical(altered), *original[2:]]) + "\n")
        report = store.verify()
        self.assertIn({"line": 2, "reason": "hash mismatch"}, report["issues"])
        with self.assertRaisesRegex(ValueError, "damaged at line 2"):
            store.list()
        with self.assertRaises(ValueError):
            store.add("new question", "Cannot hide corruption")
        store.path.write_text("\n".join([original[0], *original[2:]]) + "\n")
        self.assertTrue(any(row["line"] == 2 and "prev mismatch" in row["reason"] for row in store.verify()["issues"]))
        self.assertEqual(store.read().active, [])

    def test_malformed_versions_and_truncation(self):
        store = Store()
        store.add("staging prod database", "Use staging")
        row = json.loads(store.path.read_text())
        row.update(id="P-2", v=7, prev=hashlib.sha256(store.path.read_bytes()).hexdigest())
        row["h"] = digest(row)
        with store.path.open("a") as stream:
            stream.write(canonical(row) + '\nnot-json\n{"v":1')
        report = store.verify()
        self.assertEqual({issue["line"] for issue in report["issues"]}, {2, 3, 4})
        self.assertEqual(store.read().active, [])
        self.assertEqual(store.read().max_id, 2)

    def test_board_validation_and_core_pointer(self):
        with patch.dict(os.environ, {"HERMES_KANBAN_BOARD": "  Feature_7  "}):
            self.assertEqual(resolve_board(), "default")  # core ignores nonexistent boards
        for value in ("../outside", "a/b", "_bad", "-bad", "a" * 65):
            with self.assertRaises(ValueError):
                Store(value)
        board = self.home / "kanban" / "boards" / "named"
        board.mkdir(parents=True)
        (board / "board.json").write_text('{"name":"named"}')
        (self.home / "kanban" / "current").write_text("named\n")
        with patch.dict(os.environ, {"HERMES_KANBAN_BOARD": "", "HERMES_KANBAN_HOME": str(self.home)}):
            self.assertEqual(resolve_board(), "named")

    def test_bad_schema_is_skipped_and_lock_wait_is_bounded(self):
        store = Store()
        store.add("staging prod database", "Use staging")
        row = json.loads(store.path.read_text())
        row.update(id="P-2", op=[], prev=hashlib.sha256(store.path.read_bytes()).hexdigest())
        row["h"] = digest(row)
        with store.path.open("a") as stream:
            stream.write(canonical(row) + "\n")
        self.assertIn({"line": 2, "reason": "unknown op"}, store.verify()["issues"])
        with self.assertRaisesRegex(ValueError, "damaged at line 2"):
            store.list()
        with locked(store.lock):
            start = time.perf_counter()
            state = store.read()
            self.assertIn("busy", state.error)
            self.assertLess(time.perf_counter() - start, 0.8)

    def test_data_symlinks_do_not_redirect_writes(self):
        store = Store()
        store.directory.mkdir()
        outside = self.home / "outside.jsonl"
        outside.write_text("untouched")
        store.path.symlink_to(outside)
        self.assertFalse(store.verify()["ok"])
        with self.assertRaises(ValueError):
            store.add("staging prod", "Use staging")
        self.assertEqual(outside.read_text(), "untouched")

    def test_concurrency_eight_processes_200_rows(self):
        env = {"HOME": str(self.home), "HERMES_HOME": str(self.home), "HERMES_KANBAN_BOARD": "default",
               "TMPDIR": str(self.home), "PYTHONDONTWRITEBYTECODE": "1", "PYTHONPATH": os.pathsep.join((str(REPO), str(LAB_SOURCE)))}
        code = OFFLINE + "from precedent_log.store import Store\ns=Store()\nfor i in range(25): s.add('staging prod database', 'Use staging')"
        children = [subprocess.Popen([sys.executable, "-B", "-c", code], env=env,
                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) for _ in range(8)]
        try:
            for child in children:
                out, err = child.communicate(timeout=45)
                self.assertEqual(child.returncode, 0, out + err)
        finally:
            for child in children:
                if child.poll() is None:
                    child.kill()
                child.communicate()
        store = Store()
        lines = [json.loads(line) for line in store.path.read_text().splitlines()]
        self.assertEqual(len(lines), 200)
        self.assertEqual({row["id"] for row in lines}, {f"P-{i}" for i in range(1, 201)})
        self.assertTrue(store.verify()["ok"], store.verify())
