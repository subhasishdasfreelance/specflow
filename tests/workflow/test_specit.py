"""The specit installer and the README's uninstall block, run against a local tarball."""
import re
import shutil
import subprocess
import tarfile
import tempfile
import textwrap
import unittest
from pathlib import Path

from helpers import REPO

FAKE_CURL = '#!/usr/bin/env bash\nwhile [[ $# -gt 0 ]]; do [[ $1 == -o ]] && cp "$TARBALL" "$2"; shift; done\n'


def uninstall_script():
    section = (REPO / "README.md").read_text().split("## Uninstall", 1)[1].split("\n## ", 1)[0]
    block = re.search(r"```bash\n(.*?)```", section, re.S).group(1)
    return textwrap.dedent(block)


class SpecitTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)
        # A tarball shaped like GitHub's: one top folder holding the repo's tracked files.
        tracked = subprocess.run(["git", "ls-files", ".claude", "README.md", "guidelines.md", "CLAUDE.md"],
                                 cwd=REPO, capture_output=True, text=True, check=True).stdout.split()
        if "guidelines.md" not in tracked:
            tracked.append("guidelines.md")  # not committed yet
        self.tarball = self.tmp / "repo.tar.gz"
        with tarfile.open(self.tarball, "w:gz") as tar:
            for rel in tracked:
                tar.add(REPO / rel, arcname=f"owner-specit-abc123/{rel}")
        bin_dir = self.tmp / "bin"
        bin_dir.mkdir()
        (bin_dir / "curl").write_text(FAKE_CURL)
        (bin_dir / "curl").chmod(0o755)
        self.env = {"PATH": f"{bin_dir}:/usr/bin:/bin", "GITHUB_TOKEN": "x", "TARBALL": str(self.tarball)}
        self.project = self.tmp / "project"
        self.project.mkdir()
        self.guidelines = (REPO / "guidelines.md").read_text().rstrip("\n")

    def install(self, answer="y"):
        return subprocess.run([str(REPO / "specit")], cwd=self.project, env=self.env, input=answer + "\n",
                              capture_output=True, text=True, check=True).stdout

    def uninstall(self):
        subprocess.run(["bash", "-c", uninstall_script()], cwd=self.project, check=True)

    def read(self, name):
        return (self.project / name).read_text()

    def snapshot(self):
        return {p.relative_to(self.project).as_posix(): p.read_bytes()
                for p in self.project.rglob("*") if p.is_file()}

    def test_fresh_project(self):
        out = self.install()
        self.assertIn("new        CLAUDE.md", out)
        self.assertEqual(self.read("CLAUDE.md"), f"<!-- specit:start -->\n{self.guidelines}\n<!-- specit:end -->\n")
        self.assertEqual(self.read(".gitignore"),
                         "# specit:start\n.claude/runtime/\n.claude/settings.local.json\n# specit:end\n")
        self.assertEqual(self.read("README-specit.md"), (REPO / "README.md").read_text())
        self.assertFalse((self.project / "README.md").exists())
        self.assertFalse((self.project / "guidelines.md").exists())
        self.assertTrue((self.project / ".claude/hooks/workflow_policy.py").is_file())

        self.uninstall()
        self.assertEqual(list(self.project.iterdir()), [])

    def test_existing_files_kept_and_rerun_replaces_block(self):
        (self.project / "CLAUDE.md").write_text("# My rules\nBe nice.\n")
        (self.project / "README.md").write_text("# My app\n")
        (self.project / ".gitignore").write_text("node_modules/\n")
        (self.project / ".claude/agents").mkdir(parents=True)
        (self.project / ".claude/agents/mine.md").write_text("mine\n")
        before = self.snapshot()

        self.assertIn("append     CLAUDE.md", self.install())
        self.assertIn("update     CLAUDE.md", self.install())
        claude = self.read("CLAUDE.md")
        self.assertTrue(claude.startswith("# My rules\nBe nice.\n<!-- specit:start -->\n"))
        self.assertEqual(claude.count("specit:start"), 1)
        self.assertEqual(self.read(".gitignore").count("specit:start"), 1)
        self.assertEqual(self.read("README.md"), "# My app\n")

        self.uninstall()
        self.assertEqual(self.snapshot(), before)

    def test_answer_no_changes_nothing(self):
        (self.project / "CLAUDE.md").write_text("mine\n")
        before = self.snapshot()
        self.assertIn("Cancelled.", self.install(answer="n"))
        self.assertEqual(self.snapshot(), before)


if __name__ == "__main__":
    unittest.main()
