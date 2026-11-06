"""No-gateway lab adapter: CLI management and core dispatch with a local spawner.

The v0.23.0 default CLI dispatcher spawns an owner client, which starts a gateway.
This harness instead supplies dispatch_once's existing spawn_fn parameter. The
child runs the real AIAgent loop, tools, hooks and board transitions. This is a
pin-specific integration fixture, not the standard CLI worker launch path.
"""
import dataclasses
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import traceback

HERE = Path(__file__).resolve().parent
sys.path.insert(0, os.environ["PRECEDENT_DEMO_SOURCE"])


def dump(path, value):
    text = json.dumps(value, indent=2, default=str)
    key = os.environ.get(os.environ.get("PRECEDENT_DEMO_KEY_NAME", ""), "")
    if key:
        text = text.replace(key, "[REDACTED]")
    Path(path).write_text(text + "\n")


def worker(spec, *, warmup=False):
    from hermes_cli.plugins import get_plugin_manager
    from hermes_cli.runtime_provider import resolve_runtime_provider
    from run_agent import AIAgent
    record = {"pid": os.getpid(), "session_id": spec["session_id"], "task_id": spec.get("task_id"),
              "run_id": spec.get("run_id"), "plugins": [], "warmup": warmup}
    agent = None
    code = 1
    try:
        manager = get_plugin_manager()
        manager.discover_and_load()
        record["plugins"] = [p["name"] for p in manager.list_plugins() if p.get("enabled")]
        runtime = resolve_runtime_provider(
            requested=spec["provider"], target_model=spec["model"],
            explicit_api_key=os.environ[os.environ["PRECEDENT_DEMO_KEY_NAME"]],
            explicit_base_url=spec.get("base_url"))
        agent = AIAgent(model=spec["model"], provider=runtime["provider"],
                        api_key=runtime["api_key"], base_url=runtime["base_url"],
                        api_mode=runtime.get("api_mode"), requested_provider=spec["provider"],
                        session_id=spec["session_id"], platform="cli", cwd=spec["workspace"],
                        enabled_toolsets=["file", "kanban"], max_iterations=16,
                        quiet_mode=True, skip_memory=True, skip_context_files=True,
                        skip_background_review=True, run_budget_seconds=spec["timeout"])
        if warmup:
            record["initialized"] = True
            code = 0
        else:
            record["result"] = agent.run_conversation(spec["prompt"])
            code = int(bool(record["result"].get("error") or record["result"].get("failed")))
    except BaseException as exc:
        record["error"] = f"{type(exc).__name__}: {exc}"
        record["traceback"] = traceback.format_exc()
    finally:
        if agent is not None:
            try:
                agent.close()
            except Exception as exc:
                record["close_error"] = f"{type(exc).__name__}: {exc}"
                code = 1
        record["exit_code"] = code
        dump(spec["result_file"], record)
        print(f"[{'runtime-warmup' if warmup else 'kanban-worker-exit'}] rc={code}", flush=True)
    return code


def dispatch(spec):
    from hermes_cli import kanban_db as kb, kanban_db_connect as kbc
    from hermes_cli.kanban_db_dispatch import dispatch_once
    spawned = []
    processes = []

    def spawn(task, workspace, board=None):
        attempt = len(list(Path(spec["attempt_dir"]).glob("*-spec.json"))) + 1
        stem = Path(spec["attempt_dir"]) / f"{attempt:03d}-{task.id}"
        with kbc.connect_closing(board=board) as conn:
            comments = [dataclasses.asdict(c) for c in kb.list_comments(conn, task.id)]
        item = {**spec, "task_id": task.id, "run_id": task.current_run_id,
                "workspace": workspace, "session_id": f"demo-{task.id}-{task.current_run_id}",
                "result_file": str(stem) + "-result.json",
                "prompt": f"Work Kanban task {task.id}.\n{task.title}\n{task.body}\n"
                          f"Card comments: {json.dumps(comments)}\n"
                          f"Workspace: {workspace}\nUse the real kanban tools to finish or block."}
        dump(str(stem) + "-spec.json", item)
        env = dict(os.environ, HERMES_KANBAN_TASK=task.id, HERMES_KANBAN_BOARD=board,
                   HERMES_KANBAN_DB=str(kb.kanban_db_path(board=board)),
                   HERMES_KANBAN_RUN_ID=str(task.current_run_id),
                   HERMES_KANBAN_CLAIM_LOCK=task.claim_lock,
                   HERMES_KANBAN_WORKSPACE=workspace, TERMINAL_CWD=workspace,
                   HERMES_SESSION_SOURCE="kanban")
        log_path = kb.worker_logs_dir(board=board) / f"{task.id}.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("ab") as log:
            process = subprocess.Popen([sys.executable, "-B", str(HERE / "runtime.py"),
                                        "worker", str(stem) + "-spec.json"],
                                       env=env, cwd=workspace, stdin=subprocess.DEVNULL,
                                       stdout=log, stderr=log)
        processes.append(process)
        spawned.append({"task_id": task.id, "run_id": task.current_run_id, "pid": process.pid,
                        "spec_file": str(stem) + "-spec.json", "result_file": item["result_file"],
                        "worker_log": str(log_path)})
        dump(spec["dispatch_result"], {"spawned": spawned, "phase": "spawned"})
        return process.pid

    try:
        with kbc.connect_closing(board=spec["board"]) as conn:
            result = dispatch_once(conn, spawn_fn=spawn, board=spec["board"], max_spawn=1,
                                   max_in_progress=1, failure_limit=3)
        record = {"core_dispatch": dataclasses.asdict(result), "spawned": spawned}
        for process, item in zip(processes, spawned):
            try:
                item["exit_code"] = process.wait(timeout=spec["timeout"])
            except subprocess.TimeoutExpired:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
                item.update(exit_code=process.returncode, timed_out=True)
        dump(spec["dispatch_result"], record)
        return 0
    finally:
        for process in processes:
            if process.poll() is None:
                process.kill()
                process.wait()


if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "cli":
        sys.argv = ["hermes", *sys.argv[2:]]
        from hermes_cli.main import main
        raise SystemExit(main())
    spec = json.loads(Path(sys.argv[2]).read_text())
    if mode in {"worker", "warmup"}:
        # Keep model/SDK error output from writing an echoed key to the worker
        # log. Buffer this bounded local turn, then redact before any output.
        import contextlib
        captured = io.StringIO()
        with contextlib.redirect_stdout(captured), contextlib.redirect_stderr(captured):
            try:
                code = worker(spec, warmup=mode == "warmup")
            except BaseException:
                traceback.print_exc()
                code = 1
                print("[kanban-worker-exit] rc=1")
        key = os.environ.get(os.environ.get("PRECEDENT_DEMO_KEY_NAME", ""), "")
        output = captured.getvalue()
        print(output.replace(key, "[REDACTED]") if key else output, end="", flush=True)
        raise SystemExit(code)
    raise SystemExit(dispatch(spec))
