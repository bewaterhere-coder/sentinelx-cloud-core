from __future__ import annotations

import importlib.util
import subprocess
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("broker", HERE / "broker.py")
broker = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(broker)


class BrokerTests(unittest.TestCase):
    def cfg(self, root: Path):
        return {
            "allowed_roots": [str(root)],
            "allow_push": True,
            "timeout_seconds": 5,
            "max_timeout_seconds": 10,
            "force_http_1_1": False,
        }

    def test_secret_sanitization(self):
        value = broker.sanitize("fatal https://alice:SECRET@example.com/x password=hunter2")
        self.assertNotIn("SECRET", value)
        self.assertNotIn("hunter2", value)
        self.assertIn("***", value)

    def test_failure_classification(self):
        self.assertEqual(
            broker.classify("fatal: Recv failure: Connection was reset"),
            ("INTERRUPTED", "GitTransportReset"),
        )
        self.assertEqual(
            broker.classify("fatal: Cannot prompt because user interactivity has been disabled."),
            ("BLOCKED", "GitCredentialInteractiveRequired"),
        )
        self.assertEqual(
            broker.classify("", timed_out=True),
            ("INTERRUPTED", "GitTransportTimeout"),
        )

    def test_path_escape_is_blocked(self):
        with tempfile.TemporaryDirectory() as allowed, tempfile.TemporaryDirectory() as outside:
            with self.assertRaises(broker.BrokerError) as cm:
                broker.resolve_repo(outside, self.cfg(Path(allowed)))
            self.assertEqual(cm.exception.reason_code, "GitBrokerPathNotAllowed")

    def test_local_remote_preflight_push_fetch(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            origin = root / "origin.git"
            work = root / "work"
            subprocess.run(["git", "init", "-q", "--bare", str(origin)], check=True)
            subprocess.run(["git", "init", "-q", str(work)], check=True)
            subprocess.run(["git", "-C", str(work), "remote", "add", "origin", str(origin)], check=True)
            (work / "a.txt").write_text("one\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(work), "add", "a.txt"], check=True)
            subprocess.run(
                ["git", "-C", str(work), "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "one"],
                check=True,
            )
            cfg = self.cfg(root)

            pre = broker.handle(
                {"operation": "preflight", "repo": str(work), "remote": "origin", "timeout_seconds": 5}, cfg
            )
            self.assertTrue(pre["ok"])
            self.assertEqual(pre["state"], "READY")
            self.assertEqual(pre["capability"], "host_runtime.git_authenticated_v1")

            pushed = broker.handle(
                {"operation": "push", "repo": str(work), "remote": "origin", "branch": "main", "source": "HEAD", "timeout_seconds": 5}, cfg
            )
            self.assertTrue(pushed["ok"])

            fetched = broker.handle(
                {"operation": "fetch", "repo": str(work), "remote": "origin", "timeout_seconds": 5}, cfg
            )
            self.assertTrue(fetched["ok"])

    def test_force_requires_lease(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            repo = root / "repo"
            subprocess.run(["git", "init", "-q", str(repo)], check=True)
            subprocess.run(["git", "-C", str(repo), "remote", "add", "origin", str(root / "x.git")], check=True)
            with self.assertRaises(broker.BrokerError) as cm:
                broker.handle(
                    {"operation": "push", "repo": str(repo), "remote": "origin", "branch": "main", "source": "HEAD", "force": True}, self.cfg(root)
                )
            self.assertEqual(cm.exception.reason_code, "GitBrokerForceRequiresLease")


if __name__ == "__main__":
    unittest.main(verbosity=2)
