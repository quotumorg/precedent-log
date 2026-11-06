"""Test homes are created before any Hermes import; the lab is source-only."""

import atexit
import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


sys.dont_write_bytecode = True
LAB_SOURCE = Path(os.environ["HERMES_SOURCE"]) if os.environ.get("HERMES_SOURCE") else Path(
    importlib.util.find_spec("hermes_cli").origin).parent.parent
REPO = Path(__file__).resolve().parents[1]
BOOT_HOME = tempfile.TemporaryDirectory(prefix="precedent-tests-")
atexit.register(BOOT_HOME.cleanup)
os.environ["HERMES_HOME"] = BOOT_HOME.name
os.environ["HOME"] = BOOT_HOME.name
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
for key in list(os.environ):
    if key.startswith("HERMES_KANBAN_") or key in {"HERMES_DELEGATED_CHILD_CONTEXT", "HERMES_SAFE_MODE", "HERMES_TEST_STUBS"}:
        os.environ.pop(key)
sys.path[:0] = [str(REPO), str(LAB_SOURCE)]


def no_network(event, args):
    if event in {"socket.connect", "socket.bind", "socket.getaddrinfo"}:
        raise RuntimeError("Network disabled for offline tests")


sys.addaudithook(no_network)
OFFLINE = "import sys\ndef offline(event, args):\n    if event in {'socket.connect', 'socket.bind', 'socket.getaddrinfo'}: raise RuntimeError('Network disabled')\nsys.addaudithook(offline)\n"


class IsolatedTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="precedent-case-")
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)
        self.env = patch.dict(os.environ, {"HERMES_HOME": str(self.home), "HOME": str(self.home),
                                          "HERMES_KANBAN_HOME": str(self.home),
                                          "HERMES_VERIFY_ON_STOP": "0", "HERMES_KANBAN_BOARD": "default"})
        self.env.start()
        self.addCleanup(self.env.stop)

    def process(self, code, **env):
        child_env = {"HOME": str(self.home), "HERMES_HOME": str(self.home),
                     "TMPDIR": str(self.home), "HERMES_KANBAN_HOME": str(self.home),
                     "HERMES_KANBAN_BOARD": "default", "PYTHONDONTWRITEBYTECODE": "1",
                     "PYTHONPATH": os.pathsep.join((str(REPO), str(LAB_SOURCE))), **env}
        return subprocess.run([sys.executable, "-B", "-c", OFFLINE + code], env=child_env,
                              capture_output=True, text=True, timeout=45)
