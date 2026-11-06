"""Python audit-hook checks for the in-process harness only.

Subprocess execution, native network and native file access are outside these
checks. This is not an OS sandbox. Run in a throwaway home outside any repo.
The installed plugin does not import this module.
"""
import os
import sys
from pathlib import Path

sys.dont_write_bytecode = True


def audit(event, args):
    if event == "open" and isinstance(args[0], (str, bytes, os.PathLike)):
        path = Path(os.fsdecode(args[0]))
        if path.name in {".env", ".op.env", "auth.json", "credentials.json"} or path.name.startswith(".env."):
            raise FileNotFoundError("Demo uses process-environment credentials only")
        mode, flags = args[1:3]
        writing = (isinstance(mode, str) and any(c in mode for c in "wax+")) or (
            isinstance(flags, int) and flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC))
        source = os.environ.get("PRECEDENT_DEMO_SOURCE")
        if writing and source and path.resolve().is_relative_to(Path(source)):
            raise PermissionError("Demo keeps Hermes source read-only")
    if event == "subprocess.Popen":
        argv = args[1]
        words = argv if isinstance(argv, (list, tuple)) else str(argv).split()
        if any(str(w) in {"launchctl", "systemctl", "gateway", "hermes_cli.kanban_worker_client"}
               or Path(str(w)).name in {"launchctl", "systemctl"} for w in words):
            raise PermissionError("Demo does not start a gateway or service")
    if os.environ.get("PRECEDENT_DEMO_OFFLINE") != "1":
        return
    if event in {"socket.connect", "socket.bind"}:
        address = args[1]
        if not isinstance(address, tuple):
            raise PermissionError("Demo fake mode permits only loopback TCP")
        host, port = address[:2]
        allowed = int(os.environ.get("PRECEDENT_DEMO_PORT", "0"))
        if host not in {"127.0.0.1", "::1"} or (event == "socket.connect" and port != allowed):
            raise PermissionError("Demo fake mode refuses external network")
    if event == "socket.getaddrinfo" and args[0] not in {"127.0.0.1", "::1", "localhost"}:
        raise PermissionError("Demo fake mode refuses external DNS")


sys.addaudithook(audit)
