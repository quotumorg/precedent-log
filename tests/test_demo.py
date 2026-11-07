"""Slow: real core dispatcher and AIAgent subprocesses, loopback fake LLM only.

The full treatment/control pair takes more than 20 seconds. Run explicitly with
python -m unittest discover -s tests -p test_demo.py -v, or in the full suite.
"""
import support

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from support import REPO, LAB_SOURCE


def slow(test):
    test.slow = True
    return test


class DemoTests(unittest.TestCase):
    @slow
    def test_slow_fake_treatment_and_control(self):
        # Persist failed as well as successful runs. Never select only a passing take.
        output = Path(tempfile.gettempdir()) / "precedent-demo-runs"
        with tempfile.TemporaryDirectory(prefix="precedent-demo-test-") as scratch:
            root = Path(scratch)
            results = {}
            for mode in ("treatment", "control"):
                command = [sys.executable, "-B", str(REPO / "demo/run.py"),
                           "--hermes-source", str(LAB_SOURCE), "--hermes-home", str(root / mode),
                           "--out", str(output), "--model-provider", "fake", "--include-b2"]
                if mode == "control":
                    command.append("--no-plugin")
                # The harness deliberately replaces this environment before Hermes imports.
                env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "PYTHONDONTWRITEBYTECODE": "1"}
                run = subprocess.run(command, env=env, cwd=root, text=True, capture_output=True, timeout=400)
                print(run.stdout, flush=True)
                self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
                transcript_path = Path(run.stdout.rsplit("Transcript: ", 1)[1].strip())
                data = json.loads(transcript_path.read_text())
                results[mode] = data
                self.assertTrue(data["finished"])
                self.assertFalse(data["failures"])
                self.assertEqual(data["launch_path"], "core dispatch_once(spawn_fn=local AIAgent subprocess); no gateway")
                self.assertTrue(all(c["returncode"] == 0 for c in data["commands"]))
                self.assertEqual(data["schema"], 2)
                self.assertEqual(len(data["warmups"]), 1)
                warmup = data["warmups"][0]
                self.assertEqual(warmup["returncode"], 0)
                self.assertTrue(warmup["runtime"]["initialized"])
                self.assertIsNone(warmup["runtime"]["task_id"])
                self.assertNotIn("result", warmup["runtime"])
                self.assertTrue(all("Work Kanban task " in str(r["body"]) for r in data["fake_requests"]))
                self.assertTrue(all(a["exit_code"] == 0 for a in data["attempts"]))
                self.assertEqual(len({a["pid"] for a in data["attempts"]}), len(data["attempts"]))
                first = next(s for s in data["steps"] if s["label"] == "T1" and s["phase"] == "attempt-1")
                self.assertEqual((first["state"], first["block_kind"], first["output_present"]), ("blocked", "needs_input", False))
                self.assertEqual(data["cards"]["T1"]["state"], "done")
                self.assertTrue(data["cards"]["T1"]["output_present"])
                for label in ("T3", "T4"):
                    card = data["cards"][label]
                    self.assertEqual((card["state"], card["block_kind"], card["output_present"]), ("blocked", "needs_input", False))
                    self.assertFalse(card["citation_found"])
                    self.assertIsNone(card["citation_path"])
                self.assertTrue(all("citation_path" in step for step in data["steps"]))
                self.assertIn("path=veto" if mode == "treatment" else "path=.", run.stdout)
                self.assertNotIn("sk-demo-loopback", transcript_path.read_text())
                self.assertFalse(any((root / mode).rglob(".env")))
                for attempt in data["attempts"]:
                    if mode == "treatment":
                        self.assertIn("precedent-log", attempt["worker"]["plugins"])
                    else:
                        self.assertNotIn("precedent-log", attempt["worker"]["plugins"])

            treated = results["treatment"]
            control = results["control"]
            self.assertEqual(treated["tasks_sha256"], control["tasks_sha256"])
            self.assertEqual(treated["model"], control["model"])
            t2 = treated["cards"]["T2"]
            self.assertEqual(t2["state"], "done")
            self.assertTrue(t2["citation_found"])
            self.assertTrue(t2["summary_citation_found"])
            self.assertTrue(t2["output_citation_found"])
            self.assertEqual(t2["citation_path"], "veto")
            self.assertIn("per precedent P-1", Path(t2["output_file"]).read_text())
            self.assertIn("Target: staging", t2["output_content"])
            self.assertFalse(any(e["kind"] == "blocked" for e in t2["card"]["events"]))
            self.assertEqual(control["cards"]["T2"]["state"], "blocked")
            self.assertFalse(control["cards"]["T2"]["output_present"])
            self.assertFalse(control["cards"]["T2"]["citation_found"])
            self.assertIsNone(control["cards"]["T2"]["citation_path"])
            self.assertIn("no precedent applies: P-1", treated["cards"]["T3"]["last_reason_or_summary"])
            self.assertIn("fresh permission", treated["cards"]["T3"]["last_reason_or_summary"])
            self.assertIn("checked 0 active rulings", treated["cards"]["T4"]["last_reason_or_summary"])
            b2 = [a for a in treated["attempts"] if a["label"] == "B2"]
            self.assertEqual(len(b2), 3)
            self.assertEqual([a["card_after_exit"]["state"] for a in b2], ["running", "running", "blocked"])
            self.assertIn("escalated without citing candidates P-1", b2[-1]["card_after_exit"]["last_reason_or_summary"])
            self.assertTrue(all(not a["card_after_exit"]["output_present"] for a in b2))
            self.assertFalse(list(Path(b2[0]["card_after_exit"]["output_file"]).parent.iterdir()))
            b2_messages = [m for a in b2 for m in a["worker"]["result"].get("messages", [])]
            self.assertTrue(any("candidate rulings" in str(m.get("content")) and m["role"] == "tool" for m in b2_messages))
            self.assertTrue(any("Waiting for human input" in str(m.get("content")) and m["role"] == "assistant" for m in b2_messages))
            events = b2[-1]["card_after_exit"]["card"]["events"]
            self.assertEqual(sum(e["kind"] == "protocol_violation" for e in events), 2)
            commands = treated["commands"]
            add = next(c for c in commands if c["argv"][1:3] == ["precedent", "add"])
            self.assertIn("--source-task", add["argv"])
            self.assertIn(treated["cards"]["T1"]["task_id"], add["argv"])
            self.assertTrue(any(c["argv"][1:3] == ["precedent", "retire"] for c in commands))
            cited = next(c for c in commands if c['argv'][1:3] == ['precedent', 'cited-by'])
            retired = next(c for c in commands if c['argv'][1:3] == ['precedent', 'retire'])
            self.assertLess(commands.index(cited), commands.index(retired))
            self.assertIn(t2['task_id'], treated['cited_by_output'])
            self.assertIn('relied', treated['cited_by_output'])
            self.assertIn(t2['task_id'], retired['stdout'])
            self.assertIn('completed jobs cited it:', retired['stdout'])
