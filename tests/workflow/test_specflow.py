"""The specflow installer (bin/specflow.js), run from the packed npm package."""
import os
import shutil
import subprocess
import tarfile
import tempfile
import unittest
from pathlib import Path

from helpers import REPO


class SpecflowTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.packed = Path(tempfile.mkdtemp())
        subprocess.run([shutil.which("npm"), "pack", "--pack-destination", str(cls.packed)],
                       cwd=REPO, capture_output=True, check=True)
        with tarfile.open(next(cls.packed.glob("*.tgz"))) as tar:
            tar.extractall(cls.packed, filter="data")
        cls.bin = cls.packed / "package" / "bin" / "specflow.js"
        cls.node = shutil.which("node")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.packed)

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)
        self.project = self.tmp / "project"
        self.project.mkdir()
        self.block = (REPO / "CLAUDE.md").read_text(encoding="utf-8").rstrip("\n")

    def run_specflow(self, *args, answer="y", env=None):
        return subprocess.run([self.node, str(self.bin), *args], cwd=self.project, env=env or dict(os.environ),
                              input=answer + "\n", capture_output=True, encoding="utf-8")

    def install(self, answer="y"):
        result = self.run_specflow(answer=answer)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout

    def uninstall(self):
        result = self.run_specflow("--uninstall")
        self.assertEqual(result.returncode, 0, result.stderr)

    def write(self, name, text):
        path = self.project / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="")

    def read(self, name):
        return (self.project / name).read_text(encoding="utf-8")

    def snapshot(self):
        return {p.relative_to(self.project).as_posix(): p.read_bytes()
                for p in self.project.rglob("*") if p.is_file()}

    def test_fresh_project(self):
        out = self.install()
        self.assertIn("new        CLAUDE.md", out)
        self.assertEqual(self.read("CLAUDE.md"), f"<!-- specflow:start -->\n{self.block}\n<!-- specflow:end -->\n")
        self.assertEqual(self.read(".gitignore"),
                         "# specflow:start\n.claude/runtime/\n.claude/settings.local.json\n# specflow:end\n")
        self.assertEqual(self.read("README-specflow.md"), (REPO / "README.md").read_text(encoding="utf-8"))
        self.assertFalse((self.project / "README.md").exists())
        self.assertTrue((self.project / ".claude/hooks/workflow_policy.py").is_file())
        self.assertTrue((self.project / ".github/workflows/specflow-plans.yml").is_file())
        copied = list(self.snapshot())
        self.assertFalse([p for p in copied if "__pycache__" in p or "runtime" in p or "local" in p])
        self.assertFalse([p for p in copied if p.endswith(("test.yml", "publish.yml"))])

        self.uninstall()
        self.assertEqual(list(self.project.iterdir()), [])

    def test_existing_files_kept_and_rerun_replaces_block(self):
        self.write("CLAUDE.md", "# My rules\nBe nice.\n")
        self.write("README.md", "# My app\n")
        self.write(".gitignore", "node_modules/\n")
        self.write(".claude/agents/mine.md", "mine\n")
        before = self.snapshot()

        self.assertIn("append     CLAUDE.md", self.install())
        self.assertIn("update     CLAUDE.md", self.install())
        claude = self.read("CLAUDE.md")
        self.assertTrue(claude.startswith("# My rules\nBe nice.\n<!-- specflow:start -->\n"))
        self.assertEqual(claude.count("specflow:start"), 1)
        self.assertEqual(self.read(".gitignore").count("specflow:start"), 1)
        self.assertEqual(self.read("README.md"), "# My app\n")

        self.uninstall()
        self.assertEqual(self.snapshot(), before)

    def test_answer_no_changes_nothing(self):
        self.write("CLAUDE.md", "mine\n")
        before = self.snapshot()
        self.assertIn("Cancelled.", self.install(answer="n"))
        self.assertEqual(self.snapshot(), before)

    def test_missing_python3_stops(self):
        self.write("CLAUDE.md", "mine\n")
        before = self.snapshot()
        empty = self.tmp / "empty-path"
        empty.mkdir()
        env = {"PATH": str(empty)}
        if "SYSTEMROOT" in os.environ:
            env["SYSTEMROOT"] = os.environ["SYSTEMROOT"]
        result = self.run_specflow(env=env)
        self.assertEqual(result.returncode, 1)
        self.assertIn("python3", result.stderr)
        self.assertEqual(self.snapshot(), before)

    def test_old_specit_install_cleaned_up(self):
        self.write("CLAUDE.md", "# Mine\n<!-- specit:start -->\nold rules\n<!-- specit:end -->\n")
        self.write(".gitignore", "dist/\n# specit:start\n.claude/runtime/\n# specit:end\n")
        self.write("README-specit.md", "old guide\n")
        out = self.install()
        self.assertIn("remove     README-specit.md", out)
        self.assertIn("remove     CLAUDE.md (old specit block)", out)
        for name, own in [("CLAUDE.md", "# Mine\n"), (".gitignore", "dist/\n")]:
            text = self.read(name)
            self.assertTrue(text.startswith(own))
            self.assertNotIn("specit:start", text)
            self.assertEqual(text.count("specflow:start"), 1)
        self.assertNotIn("old rules", self.read("CLAUDE.md"))
        self.assertFalse((self.project / "README-specit.md").exists())

    def test_file_without_trailing_newline(self):
        self.write(".gitignore", "node_modules/")
        self.install()
        self.install()
        text = self.read(".gitignore")
        self.assertTrue(text.startswith("node_modules/\n# specflow:start\n"))
        self.assertEqual(text.count("specflow:start"), 1)
        self.uninstall()
        self.assertEqual(self.read(".gitignore"), "node_modules/\n")

    def test_old_plans_get_new_mark(self):
        self.write("tickets/feature/old.md", "📝 Users log in (src/login.py)\n  1. Keep the 📝 here.\n")
        self.assertIn("update     tickets/feature/old.md (📝 to 🔲)", self.install())
        self.assertEqual(self.read("tickets/feature/old.md"), "🔲 Users log in (src/login.py)\n  1. Keep the 📝 here.\n")

    def test_existing_workflows_untouched(self):
        self.write(".github/workflows/ci.yml", "name: ci\non: push\n")
        before = self.snapshot()
        self.install()
        self.assertEqual(self.snapshot()[".github/workflows/ci.yml"], before[".github/workflows/ci.yml"])
        self.assertTrue((self.project / ".github/workflows/specflow-plans.yml").is_file())
        self.uninstall()
        self.assertEqual(self.snapshot(), before)

    def test_unknown_argument_shows_usage(self):
        result = self.run_specflow("main")
        self.assertEqual(result.returncode, 1)
        self.assertIn("Usage: specflow [--uninstall]", result.stderr)


if __name__ == "__main__":
    unittest.main()
