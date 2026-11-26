"""scripts/release.js, run in a throwaway git repo with a bare repo as its origin."""
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from helpers import REPO


class ReleaseTest(unittest.TestCase):
    def setUp(self):
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp)
        self.origin = tmp / "origin.git"
        self.repo = tmp / "repo"
        self.git("init", "-q", "--bare", str(self.origin), cwd=tmp)
        self.git("init", "-q", "-b", "main", str(self.repo), cwd=tmp)
        for key, value in [("user.name", "Test"), ("user.email", "test@example.com"),
                           ("commit.gpgsign", "false"), ("tag.gpgsign", "false")]:
            self.git("config", key, value)
        (self.repo / "scripts").mkdir()
        shutil.copy(REPO / "scripts" / "release.js", self.repo / "scripts" / "release.js")
        self.write_version("0.1.0")
        self.git("add", ".")
        self.git("commit", "-q", "-m", "start")
        self.git("remote", "add", "origin", str(self.origin))
        self.git("push", "-q", "origin", "main")

    def git(self, *args, cwd=None):
        return subprocess.run(["git", *args], cwd=cwd or self.repo, capture_output=True,
                              text=True, check=True).stdout.strip()

    def write_version(self, version):
        (self.repo / "package.json").write_text(json.dumps({"name": "x", "version": version}, indent=2) + "\n")

    def version(self):
        return json.loads((self.repo / "package.json").read_text())["version"]

    def release(self, *args):
        return subprocess.run([shutil.which("node"), "scripts/release.js", *args], cwd=self.repo,
                              capture_output=True, text=True, encoding="utf-8")

    def test_refuses(self):
        head = self.git("rev-parse", "HEAD")
        self.assertEqual(self.release("minor").returncode, 1)
        self.assertEqual(self.release("minor", "  ").returncode, 1)
        self.assertEqual(self.release("huge", "msg").returncode, 1)

        self.git("checkout", "-q", "-b", "feature/x")
        self.assertIn("only on main", self.release("minor", "msg").stderr)
        self.git("checkout", "-q", "main")

        (self.repo / "package.json").write_text("{}\n")
        self.assertEqual(self.release("minor", "msg").returncode, 1)
        self.git("checkout", "--", "package.json")

        (self.repo / "new.txt").write_text("x\n")
        self.assertIn("new.txt", self.release("minor", "msg").stderr)

        self.assertEqual(self.git("rev-parse", "HEAD"), head)
        self.assertEqual(self.git("tag"), "")

    def test_minor_release(self):
        message = "added new option to check history"
        result = self.release("minor", message)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Released v0.2.0", result.stdout)
        self.assertEqual(self.version(), "0.2.0")
        self.assertEqual(self.git("log", "-1", "--format=%s"), message)
        self.assertEqual(self.git("cat-file", "-t", "v0.2.0"), "tag")
        self.assertEqual(self.git("tag", "-l", "--format=%(contents:subject)", "v0.2.0"), message)
        self.assertEqual(self.git("rev-parse", "main", cwd=self.origin), self.git("rev-parse", "HEAD"))
        self.assertEqual(self.git("tag", cwd=self.origin), "v0.2.0")

    def test_prerelease_steps(self):
        for kind, expected in [("alpha", "0.2.0-alpha.0"), ("alpha", "0.2.0-alpha.1"), ("beta", "0.2.0-beta.0")]:
            result = self.release(kind, f"{kind} step")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(self.version(), expected)
        self.assertEqual(self.release("alpha", "back").returncode, 1)
        self.assertEqual(self.version(), "0.2.0-beta.0")
        self.assertEqual(self.release("minor", "stable").returncode, 0)
        self.assertEqual(self.version(), "0.2.0")

    def test_stable_bumps(self):
        for kind, expected in [("patch", "0.1.1"), ("minor", "0.2.0"), ("major", "1.0.0")]:
            self.assertEqual(self.release(kind, kind).returncode, 0)
            self.assertEqual(self.version(), expected)


if __name__ == "__main__":
    unittest.main()
