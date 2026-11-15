import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from helpers import REPO, plan_text

sys.path.insert(0, str(REPO / ".claude" / "scripts"))
import validate_plan as vp  # noqa: E402


class ValidatePlanTest(unittest.TestCase):
    def test_valid_plan(self):
        self.assertEqual(vp.validate(plan_text()), [])

    def test_branch_must_match_file(self):
        self.assertEqual(vp.validate(plan_text(), "feature/login"), [])
        self.assertTrue(vp.validate(plan_text(), "bugfix/other"))

    def test_all_statuses_accepted(self):
        for s in vp.STATUSES:
            t = s if s not in vp.DONE else "Built"
            self.assertEqual(vp.validate(plan_text(s, t, t)), [], s)

    def test_invalid_plan_status(self):
        errors = vp.validate(plan_text(status="Done"))
        self.assertIn("invalid plan status 'Done'", errors)

    def test_invalid_task_status(self):
        self.assertIn("TASK-001: invalid status 'In Progress'",
                      vp.validate(plan_text(t1="In Progress")))

    def test_duplicate_task_id(self):
        text = plan_text().replace("TASK-002: Session", "TASK-001: Session")
        self.assertIn("duplicate task id TASK-001", vp.validate(text))

    def test_missing_task_field(self):
        text = plan_text().replace("- Verify: unit test\n", "", 1)
        self.assertIn("TASK-001: missing '- Verify:'", vp.validate(text))

    def test_unknown_requirement(self):
        text = plan_text().replace("- Requirements: FR-001\n", "- Requirements: FR-009\n")
        self.assertIn("TASK-001: unknown requirement FR-009", vp.validate(text))

    def test_missing_section_and_branch(self):
        text = plan_text().replace("## Risks\n", "").replace("- Branch: feature/login\n", "")
        errors = vp.validate(text)
        self.assertIn("missing section '## Risks'", errors)
        self.assertIn("missing plan field '- Branch:'", errors)

    def test_built_plan_needs_built_tasks(self):
        self.assertIn("plan is Built but TASK-002 is Building",
                      vp.validate(plan_text("Built", "Built", "Building")))

    def test_cli_exit_codes(self):
        script = REPO / ".claude" / "scripts" / "validate_plan.py"
        with tempfile.TemporaryDirectory() as d:
            good, bad = Path(d, "good.md"), Path(d, "bad.md")
            good.write_text(plan_text())
            bad.write_text(plan_text(status="Approved"))
            ok = subprocess.run([sys.executable, script, good], capture_output=True, text=True)
            fail = subprocess.run([sys.executable, script, bad], capture_output=True, text=True)
            missing = subprocess.run([sys.executable, script, Path(d, "nope.md")],
                                     capture_output=True, text=True)
        self.assertEqual(ok.returncode, 0, ok.stdout)
        self.assertEqual(fail.returncode, 1)
        self.assertIn("invalid plan status 'Approved'", fail.stdout)
        self.assertEqual(missing.returncode, 1)


if __name__ == "__main__":
    unittest.main()
