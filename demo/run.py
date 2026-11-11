#!/usr/bin/env python3
"""Reproducible local proof, with all attempts kept. See README before real use."""
import argparse
import ast
import dataclasses
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import tomllib
import uuid

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
HERMES_RANGE = ">=0.23.0,<0.24"
FIXTURES = ("migration", "dependency-upgrade", "customer-copy", "log-retention")


def load_fixture(name="migration"):
    catalog = json.loads((HERE / "tasks.json").read_text())
    if name not in FIXTURES:
        raise ValueError("Unknown fixture: " + name)
    return ({k: v for k, v in catalog.items() if k != "fixtures"}
            if name == "migration" else catalog["fixtures"][name])


def preflight(source):
    """Read-only prerequisites before creating any run output or importing Hermes."""
    if not (3, 11) <= sys.version_info[:2] < (3, 15):
        raise ValueError("Demo requires Python >=3.11,<3.15 from the prepared Hermes environment")
    source = Path(source).expanduser().resolve(strict=True)
    for name in ("hermes_cli/main.py", "run_agent.py", "pyproject.toml"):
        if not (source / name).is_file():
            raise ValueError("Complete Hermes source required; missing " + name)
    # Read metadata, never import Hermes or consult the user's installed package.
    version = tomllib.loads((source / "pyproject.toml").read_text()).get("project", {}).get("version")
    if version in (None, "0.0.0"):
        # Hermes release checkouts can have a placeholder package version.
        release = subprocess.run(["git", "-C", str(source), "describe", "--tags", "--exact-match", "--match", "v[0-9]*"],
                                 capture_output=True, text=True, timeout=10)
        version = release.stdout.strip().removeprefix("v") if release.returncode == 0 else None
    parsed = re.fullmatch(r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)", str(version))
    if not parsed or not (0, 23, 0) <= tuple(map(int, parsed.groups())) < (0, 24, 0):
        raise ValueError(f"Demo requires Hermes {HERMES_RANGE}; source version: {version or 'not recorded (need package version or exact release tag)'}")
    helper = source / "tests/fakes/fake_llm_provider.py"
    if not helper.is_file():
        raise ValueError("Complete source must include tests.fakes.fake_llm_provider")
    try:
        names = {node.name for node in ast.parse(helper.read_text()).body if isinstance(node, ast.ClassDef)}
    except (SyntaxError, UnicodeError) as exc:
        raise ValueError("Cannot parse tests.fakes.fake_llm_provider") from exc
    if not {"FakeLLMServer", "Text", "ToolCall"} <= names:
        raise ValueError("tests.fakes.fake_llm_provider lacks FakeLLMServer, Text or ToolCall")
    return source


def outside_git(path, label):
    """Check ordinary repositories and linked checkouts (whose .git is a file)."""
    resolved = Path(path).expanduser().resolve()
    for parent in (resolved, *resolved.parents):
        if (parent / ".git").exists() or (parent / ".git").is_symlink():
            raise ValueError(f"{label} must be outside any git work tree: {resolved} (found {parent / '.git'})")
    return resolved


def citation_evidence(attempts, output, ruling_id="P-1"):
    """Observe syntactic citation markers in a successful completion and output.

    Path is a tool-trace classification, not proof of the model's reasoning.
    A block without a plugin veto leaves the citation's path unclassified.
    """
    pattern = re.compile(r"\b" + re.escape(ruling_id) + r"\b", re.I)
    summary = None
    path = None
    block_seen = veto_seen = False
    for attempt in attempts:
        calls = {}
        for message in attempt.get("worker", {}).get("result", {}).get("messages", []):
            if message.get("role") == "assistant":
                for call in message.get("tool_calls", []):
                    fn = call.get("function", {})
                    try:
                        args = json.loads(fn.get("arguments", "{}"))
                    except (ValueError, TypeError):
                        continue
                    if not isinstance(args, dict):
                        continue
                    if args.get("task_id", attempt.get("task_id")) != attempt.get("task_id"):
                        continue
                    calls[call.get("id")] = (fn.get("name"), args)
                    if fn.get("name") == "kanban_block":
                        block_seen = True
            elif message.get("role") == "tool":
                name, args = calls.get(message.get("tool_call_id"), (None, {}))
                try:
                    result = json.loads(message.get("content", ""))
                except (ValueError, TypeError):
                    continue
                if not isinstance(result, dict):
                    continue
                if name == "kanban_block" and str(result.get("error", "")).startswith("[precedent-log] candidate rulings."):
                    veto_seen = True
                elif name == "kanban_complete" and result.get("ok") is True:
                    summary = str(args.get("summary") or "")
                    path = "veto" if veto_seen else (None if block_seen else "prompt")
    in_summary = bool(pattern.search(summary or ""))
    in_output = bool(pattern.search(output or ""))
    found = in_summary and in_output
    return {"completion_summary": summary, "summary_citation_found": in_summary,
            "output_citation_found": in_output, "citation_found": found,
            "citation_path": path if found else None}


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hermes-source", default=os.environ.get("HERMES_SOURCE"), required=not os.environ.get("HERMES_SOURCE"))
    parser.add_argument("--hermes-home", default=os.environ.get("HERMES_HOME"), help="New or empty lab home; otherwise created under the run directory")
    parser.add_argument("--repo", type=Path, default=REPO)
    parser.add_argument("--out", type=Path, default=Path(tempfile.gettempdir()) / "precedent-demo-runs",
                        help="Run directory parent, outside any git work tree (default: system temp/precedent-demo-runs)")
    parser.add_argument("--run-id", default=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ-") + uuid.uuid4().hex[:8])
    parser.add_argument("--model-provider", default="fake", help="fake, or a Hermes API-key provider")
    parser.add_argument("--model", help="Passed to both the task and AIAgent")
    parser.add_argument("--provider-env", help="Name of the already exported key variable; never a value or file")
    parser.add_argument("--base-url", help="Optional provider endpoint without credentials")
    parser.add_argument("--no-plugin", action="store_true")
    parser.add_argument("--fixture", choices=FIXTURES, default="migration")
    parser.add_argument("--veto", choices=("enforce", "advisory"), default="enforce",
                        help="Plugin block-check mode (default: enforce); advisory retains prompt rulings")
    parser.add_argument("--include-b2", action="store_true", help="Also observe the no-edit veto, final text and core recovery")
    parser.add_argument("--timeout", type=float, default=90, help="Seconds per worker attempt")
    parser.add_argument("--warmup-timeout", type=float, default=300,
                        help="Seconds per no-op runtime warm-up attempt before T1 (at most two starts)")
    return parser.parse_args()


class Harness:
    def __init__(self, args):
        self.args = args
        if not re.fullmatch(r"[A-Za-z0-9_-]+", args.run_id):
            raise ValueError("run-id must contain only letters, digits, underscores or hyphens")
        self.source = preflight(args.hermes_source)
        self.out = outside_git(args.out / args.run_id, "Run directory (--out)")
        self.home = outside_git(args.hermes_home or self.out / "hermes-home", "Hermes home (--hermes-home/HERMES_HOME)")
        if self.home.exists() and any(self.home.iterdir()):
            raise ValueError("Use a new or empty HERMES_HOME; existing profiles are not modified")
        self.out.mkdir(parents=True, exist_ok=False)
        self.home.mkdir(parents=True, exist_ok=True)
        print(f"Run directory: {self.out}", flush=True)
        self.board = "precedent-demo"
        self.fixture = load_fixture(args.fixture)
        self.data = {"schema": 2, "run_id": args.run_id, "plugin": not args.no_plugin,
                     "fixture": args.fixture,
                     "veto": args.veto,
                     "hermes_source": str(self.source), "hermes_home": str(self.home), "board": self.board,
                     "launch_path": "core dispatch_once(spawn_fn=local AIAgent subprocess); no gateway",
                     "model_provider": args.model_provider, "model": args.model or "fake-model",
                     "tasks_sha256": hashlib.sha256((HERE / "tasks.json").read_bytes()).hexdigest(),
                     "commands": [], "warmups": [], "steps": [], "attempts": [], "dispatches": [], "cards": {},
                     "fake_requests": [], "failures": [], "finished": False}
        self.env = {k: v for k, v in os.environ.items() if k in {"PATH", "LANG", "LC_ALL", "SYSTEMROOT"}}
        fake = args.model_provider == "fake"
        key_name = "OPENAI_API_KEY" if fake else args.provider_env
        if not key_name or (not fake and not os.environ.get(key_name)):
            raise ValueError("Real runs require --provider-env naming an already exported API key")
        if not fake and not args.model:
            raise ValueError("Real runs require --model")
        self.secret = "sk-demo-loopback" if fake else os.environ[key_name]
        for directory in ("os-home", "tmp", "attempts"):
            (self.out / directory).mkdir()
        self.env.update(HOME=str(self.out / "os-home"), HERMES_HOME=str(self.home),
                        HERMES_KANBAN_HOME=str(self.home), HERMES_KANBAN_BOARD=self.board,
                        TMPDIR=str(self.out / "tmp"), XDG_CACHE_HOME=str(self.out / "os-home/cache"),
                        PYTHONDONTWRITEBYTECODE="1", PYTHONPATH=os.pathsep.join([str(HERE / "sandbox"), str(self.source)]),
                        PRECEDENT_DEMO_SOURCE=str(self.source), PRECEDENT_DEMO_OFFLINE="1" if fake else "0",
                        PRECEDENT_DEMO_KEY_NAME=key_name, HERMES_KANBAN_CRASH_GRACE_SECONDS="0",
                        NO_COLOR="1", TERM="dumb", TOKENIZERS_PARALLELISM="false")
        self.env[key_name] = self.secret
        # Set isolation before importing even the fake server's Hermes dependencies.
        os.environ.clear()
        os.environ.update(self.env)
        sys.path[:0] = [str(HERE / "sandbox"), str(self.source)]
        import sitecustomize  # noqa: F401
        self.tasks = {}
        self.answered = False
        self.server = None
        self.save()

    def clean(self, value):
        return json.loads(json.dumps(value, default=str).replace(self.secret, "[REDACTED]"))

    def save(self):
        if self.server:
            # Deliberately exclude headers/auth from the FakeLLMServer record.
            self.data["fake_requests"] = self.clean([
                {k: r[k] for k in ("kind", "body", "t", "response", "scripted_response") if k in r}
                for r in self.server.requests])
        target = self.out / "transcript.json"
        temporary = target.with_suffix(".tmp")
        temporary.write_text(json.dumps(self.clean(self.data), indent=2) + "\n")
        temporary.replace(target)

    def command(self, args, *, check=True, echo=False):
        argv = [sys.executable, "-B", str(HERE / "runtime.py"), "cli", *args]
        if echo:
            print("$ " + shlex.join(["env", f"HERMES_HOME={self.home}",
                                   f"HERMES_KANBAN_BOARD={self.board}", "hermes", *args]), flush=True)
        row = {"argv": ["hermes", *args], "started_at": time.time()}
        self.data["commands"].append(row)
        self.save()
        try:
            result = subprocess.run(argv, cwd=self.out, env=self.env, stdin=subprocess.DEVNULL,
                                    capture_output=True, text=True, timeout=self.args.timeout)
            row.update(returncode=result.returncode, stdout=result.stdout, stderr=result.stderr)
        except subprocess.TimeoutExpired as exc:
            row.update(returncode=None, error="command timed out", stdout=str(exc.stdout or ""), stderr=str(exc.stderr or ""))
            self.save()
            raise
        self.save()
        if check and result.returncode:
            raise RuntimeError(self.clean(f"Command failed: {shlex.join(args)}\n{result.stdout}\n{result.stderr}"))
        return result

    @staticmethod
    def json_output(text):
        decoder = json.JSONDecoder()
        for index, char in enumerate(text):
            if char == "{":
                try:
                    return decoder.raw_decode(text[index:])[0]
                except ValueError:
                    pass
        raise ValueError("CLI did not return a JSON object")

    def snapshot(self, label, phase, *, announce=True):
        task = self.tasks[label]
        card = self.json_output(self.command(["kanban", "show", task["id"], "--json"]).stdout)
        workspace = Path(card["task"]["workspace_path"] or task["workspace"])
        output = workspace / task["output"]
        latest = card.get("latest_summary") or card["task"].get("block_reason") or ""
        if isinstance(latest, dict):
            latest = latest.get("summary", str(latest))
        file_text = output.read_text() if output.is_file() else None
        # v0.23.0 has no task.block_kind; use the committed event payload.
        blocks = [e for e in card["events"] if e["kind"] == "blocked"]
        block_kind = blocks[-1]["payload"].get("kind") if blocks and card["task"]["status"] == "blocked" else None
        step = {"label": label, "phase": phase, "fixture": self.args.fixture,
                "task_id": task["id"], "state": card["task"]["status"],
                "block_kind": block_kind, "last_reason_or_summary": latest,
                **citation_evidence([a for a in self.data["attempts"] if a["label"] == label], file_text),
                "output_file": str(output), "output_present": output.is_file(), "output_content": file_text,
                "card": card}
        self.data["cards"][label] = step
        self.data["steps"].append(step)
        self.save()
        if announce:
            reason = " ".join(latest.split())
            print(f"{label} {phase} | {step['state']} | {step['block_kind'] or '.'} | "
                  f"{reason} | citation={step['citation_found']} | path={step['citation_path'] or '.'} | "
                  f"output={step['output_present']} | mode={self.args.veto} | fixture={self.args.fixture}", flush=True)
        return step

    def warm_up(self):
        """Initialize and close AIAgent without a conversation or task claim.

        A dependency activation may require a fresh process. Keep the failed
        start and retry once; never spend T1's retry budget on runtime setup.
        """
        for number in (1, 2):
            stem = self.out / "attempts" / f"warmup-{number}"
            spec = {"provider": self.provider, "model": self.data["model"], "base_url": self.base_url,
                    "timeout": self.args.warmup_timeout, "session_id": f"warmup-{number}",
                    "workspace": str(self.out), "result_file": str(stem) + "-result.json"}
            spec_path = Path(str(stem) + ".json")
            spec_path.write_text(json.dumps(spec))
            argv = [sys.executable, "-B", str(HERE / "runtime.py"), "warmup", str(spec_path)]
            row = {"attempt": number, "argv": argv, "started_at": time.time()}
            self.data["warmups"].append(row)
            self.save()
            process = subprocess.Popen(argv, cwd=self.out, env=self.env, stdin=subprocess.DEVNULL,
                                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                                       start_new_session=True)
            row["pid"] = process.pid
            self.save()
            try:
                stdout, stderr = process.communicate(timeout=self.args.warmup_timeout)
            except (subprocess.TimeoutExpired, KeyboardInterrupt) as exc:
                os.killpg(process.pid, signal.SIGKILL)
                stdout, stderr = process.communicate()
                row["error"] = type(exc).__name__
                if isinstance(exc, KeyboardInterrupt):
                    row.update(returncode=process.returncode, stdout=stdout, stderr=stderr)
                    self.save()
                    raise
            result_path = Path(spec["result_file"])
            row.update(returncode=process.returncode, stdout=stdout, stderr=stderr,
                       elapsed_seconds=time.time() - row["started_at"],
                       runtime=json.loads(result_path.read_text()) if result_path.exists() else {"error": "warm-up result missing"})
            self.save()
            print(f"Warm-up {number} | rc={process.returncode} | no conversation or task claim", flush=True)
            if process.returncode == 0 and row["runtime"].get("initialized"):
                return
        raise RuntimeError("Runtime warm-up failed twice; T1 was not created. Inspect transcript warmups and use an installed Hermes runtime.")

    def create(self, task):
        workspace = self.out / "workspaces" / task["label"]
        workspace.mkdir(parents=True)
        result = self.command(["kanban", "create", task["title"], "--body", task["body"],
                               "--assignee", "default", "--workspace", f"dir:{workspace}",
                               "--model", self.data["model"], "--provider", self.provider,
                               "--max-retries", "3", "--json"])
        task_id = self.json_output(result.stdout)["id"]
        self.tasks[task["label"]] = {**task, "id": task_id, "workspace": str(workspace)}
        self.snapshot(task["label"], "created", announce=False)

    def run_task(self, label):
        for attempt in range(1, 5):
            tick = len(self.data["dispatches"]) + 1
            path = self.out / "attempts" / f"dispatch-{tick}.json"
            spec = {"board": self.board, "provider": self.provider, "model": self.data["model"],
                    "base_url": self.base_url, "timeout": self.args.timeout,
                    "attempt_dir": str(self.out / "attempts"), "dispatch_result": str(path)}
            spec_path = self.out / "attempts" / f"tick-{tick}.json"
            spec_path.write_text(json.dumps(spec))
            row = {"label": label, "tick": tick, "result_file": str(path)}
            self.data["dispatches"].append(row)
            self.save()
            process = subprocess.Popen([sys.executable, "-B", str(HERE / "runtime.py"), "dispatch", str(spec_path)],
                                       cwd=self.out, env=self.env, stdin=subprocess.DEVNULL,
                                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                                       start_new_session=True)
            try:
                stdout, stderr = process.communicate(timeout=self.args.timeout + 30)
            except (subprocess.TimeoutExpired, KeyboardInterrupt) as exc:
                # Only this harness-owned process group. Preserve its spawn
                # record even if the dispatcher cannot finish its JSON report.
                os.killpg(process.pid, signal.SIGKILL)
                stdout, stderr = process.communicate()
                row["error"] = type(exc).__name__
            row.update(returncode=process.returncode, stdout=stdout, stderr=stderr)
            detail = json.loads(path.read_text()) if path.exists() else {}
            row["detail"] = detail
            for spawn in detail.get("spawned", []):
                record = {"label": label, **spawn}
                result_file = Path(spawn["result_file"])
                record["worker"] = json.loads(result_file.read_text()) if result_file.exists() else {"error": "worker result missing"}
                record["log"] = Path(spawn["worker_log"]).read_text(errors="replace")
                if "error" in row:
                    record["dispatcher_error"] = row["error"]
                self.data["attempts"].append(record)
            final = self.snapshot(label, f"attempt-{attempt}")
            for record in self.data["attempts"]:
                if record.get("card_after_exit") is None and record["label"] == label:
                    record["card_after_exit"] = final
            self.save()
            if process.returncode:
                raise RuntimeError(self.clean(f"Dispatcher failed ({process.returncode}): {stderr}"))
            if final["state"] in {"done", "blocked", "failed", "triage"}:
                return final
            # The next real core tick observes the exited PID and its exit trailer.
            # No synthetic PID, forced reclaim, card edit or policy reset.
        self.data["failures"].append(f"{label}: attempt budget exhausted")
        return final

    def respond(self, request):
        from tests.fakes.fake_llm_provider import Text, ToolCall
        messages = request["body"]["messages"]
        user_text = "\n".join(str(m.get("content", "")) for m in messages if m.get("role") == "user")
        task = next((t for t in self.tasks.values() if f"Work Kanban task {t['id']}." in user_text), None)
        if task is None:
            response = Text("No recognized demo task.")
        else:
            label = task["label"]
            calls = [call for m in messages if m.get("role") == "assistant" for call in m.get("tool_calls", [])]
            names = [call["function"]["name"] for call in calls]
            tool_text = "\n".join(str(m.get("content", "")) for m in messages if m.get("role") == "tool")
            candidate = "candidate rulings" in tool_text
            block_args = {"kind": "needs_input", "reason": task["reason"]}
            script = self.fixture.get("fake", {})
            plan = f"# {task['title']}\nTarget: staging\nPlan only; no SQL was executed.\n" \
                   "1. Back up the rehearsal dataset.\n2. Rehearse the nullable column addition on staging.\n" \
                   "3. Validate row counts and backwards compatibility.\n4. Roll back the rehearsal if validation fails.\n" \
                   "Production operations require fresh approval.\n"
            plan = script.get("plan", plan)
            if label == "T1" and self.answered:
                if "kanban_show" not in names:
                    response = ToolCall("kanban_show", {})
                elif "write_file" not in names:
                    response = ToolCall("write_file", {"path": task["output"], "content": plan + "Source: human answer on this card.\n"})
                elif "kanban_complete" not in names:
                    response = ToolCall("kanban_complete", {"summary": script.get("summary_t1", "Human answer used: staging; users-plan.md written."), "artifacts": [task["output"]]})
                else:
                    response = Text("Local plan delivered.")
            elif label in {"T2", "T3", "T4"} and "write_file" not in names:
                response = ToolCall("write_file", {"path": "draft.md", "content": script.get("draft", "Local schema migration checklist.\nTarget unresolved.\nBack up, rehearse, validate, roll back.\n")})
            elif "kanban_block" not in names:
                response = ToolCall("kanban_block", block_args)
            elif label == "T2" and candidate:
                if names.count("write_file") < 2:
                    response = ToolCall("write_file", {"path": task["output"], "content": plan + "Decision source: per precedent P-1.\n"})
                elif "kanban_complete" not in names:
                    response = ToolCall("kanban_complete", {"summary": script.get("summary_t2", "per precedent P-1: staging chosen; orders-plan.md written. No operations authorized."), "artifacts": [task["output"]]})
                else:
                    response = Text("Plan delivered per precedent P-1.")
            elif label == "T3" and candidate and names.count("kanban_block") == 1:
                response = ToolCall("kanban_block", {**block_args, "reason": task["reason"] + " no precedent applies: " + script.get("rejection", "P-1 chooses the environment for a local plan; it does not grant fresh permission to drop a production column.")})
            else:
                response = Text("Waiting for human input after the tool result; no edits made." if label == "B2" else "Waiting for human input.")
        request["scripted_response"] = {"type": type(response).__name__, **dataclasses.asdict(response)}
        return response

    def execute(self, base_url):
        self.base_url = base_url
        self.provider = "custom" if self.args.model_provider == "fake" else self.args.model_provider
        if self.server:
            self.env["PRECEDENT_DEMO_PORT"] = str(self.server.port)
            os.environ["PRECEDENT_DEMO_PORT"] = str(self.server.port)
        config = {"model": {"provider": self.provider, "default": self.data["model"], "context_length": 128000},
                  "agent": {"api_max_retries": 1}, "updates": {"check": False},
                  "terminal": {"env_type": "local"}, "kanban": {"dispatch_in_gateway": False},
                  "telemetry": {"shared_metrics": {"enabled": False, "send": False, "offer_version": 999}},
                  "plugins": {"enabled": [] if self.args.no_plugin else ["precedent-log"], "isolation": "in_process",
                              "entries": {"precedent-log": {"settings": {"precedent_log": {"veto": self.args.veto}}}}}}
        if base_url:
            config["model"]["base_url"] = base_url
        (self.home / "config.yaml").write_text(json.dumps(config, indent=2))
        if not self.args.no_plugin:
            destination = self.home / "plugins/precedent-log"
            destination.mkdir(parents=True)
            for name in ("__init__.py", "plugin.yaml", "LICENSE"):
                shutil.copy2(self.args.repo / name, destination / name)
            shutil.copytree(self.args.repo / "precedent_log", destination / "precedent_log",
                            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        self.command(["kanban", "boards", "create", self.board])
        self.warm_up()
        self.create(self.fixture["tasks"][0])
        initial = self.run_task("T1")
        if (initial["state"], initial["block_kind"], initial["output_present"]) != ("blocked", "needs_input", False):
            self.data["failures"].append("T1: expected an unanswered needs_input block before any output")
        if not self.args.no_plugin:
            self.command(["precedent", "add", "--board", self.board, "--question", self.fixture["question"],
                          "--ruling", self.fixture["ruling"], "--keys", self.fixture["keys"],
                          "--source-task", self.tasks["T1"]["id"]], echo=True)
        else:
            print("Control: no ruling stored; only the T1 card receives the human answer.", flush=True)
        result = self.command(["kanban", "unblock", self.tasks["T1"]["id"], "--reason", self.fixture["ruling"]], check=False, echo=True)
        self.snapshot("T1", "human-answer")
        if result.returncode == 0:
            self.answered = True
            self.run_task("T1")
        else:
            self.data["failures"].append("T1: core unblock failed; ruling add and unblock are separate operations")
        for task in self.fixture["tasks"][1:3]:
            self.create(task)
            self.run_task(task["label"])
        if self.args.include_b2:
            self.create(self.fixture["b2"])
            self.run_task("B2")
        if not self.args.no_plugin:
            cited_by = self.command(['precedent', 'cited-by', 'P-1', '--board', self.board], echo=True)
            self.data['cited_by_output'] = cited_by.stdout
            print(cited_by.stdout.strip(), flush=True)
            retired = self.command(["precedent", "retire", "P-1", "--board", self.board,
                                    "--reason", "Demo retirement: require a new decision."], echo=True)
            print(retired.stdout.strip(), flush=True)
        self.create(self.fixture["tasks"][3])
        self.run_task("T4")
        self.data["finished"] = True
        expected = {"T1": "done", "T2": "blocked" if self.args.no_plugin else "done", "T3": "blocked", "T4": "blocked"}
        # Advisory observes prompt-only reuse or an allowed re-ask; neither is a veto failure.
        if not self.args.no_plugin and self.args.veto == "advisory":
            second_state = self.data["cards"]["T2"]["state"]
            expected["T2"] = second_state if second_state in {"done", "blocked"} else "done"
        for label, state in expected.items():
            actual = self.data["cards"][label]
            if actual["state"] != state or actual["output_present"] != (state == "done"):
                self.data["failures"].append(f"{label}: expected {state} with artifact if done; observed {actual['state']}")
            if state == "blocked" and actual["block_kind"] != "needs_input":
                self.data["failures"].append(f"{label}: expected needs_input, observed {actual['block_kind']}")
        if not self.args.no_plugin:
            second = self.data["cards"]["T2"]
            if expected["T2"] == "done" and not second["citation_found"]:
                self.data["failures"].append("T2: missing P-1 citation in completion or output")
            third = self.data["cards"]["T3"]["last_reason_or_summary"]
            if self.args.veto == "enforce" and ("no precedent applies:" not in third.lower() or "P-1" not in third):
                self.data["failures"].append("T3: missing explicit P-1 rejection")
        self.save()


def main():
    try:
        harness = Harness(parse_args())
    except (ValueError, OSError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    try:
        if harness.args.model_provider == "fake":
            from tests.fakes.fake_llm_provider import FakeLLMServer
            with FakeLLMServer(harness.respond) as server:
                harness.server = server
                harness.execute(server.base_url)
        else:
            harness.execute(harness.args.base_url)
    except BaseException as exc:
        harness.data["failures"].append(harness.clean(f"{type(exc).__name__}: {exc}"))
        harness.save()
        print(harness.clean(str(exc)), file=sys.stderr)
        return 1
    finally:
        harness.save()
        print(f"Transcript: {harness.out / 'transcript.json'}", flush=True)
    return int(bool(harness.data["failures"]))


if __name__ == "__main__":
    raise SystemExit(main())
