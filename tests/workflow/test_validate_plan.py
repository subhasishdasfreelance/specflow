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

    def test_all_statuses_accepted(self):
        for s in vp.STATUSES:
            self.assertEqual(vp.validate(plan_text(s, done=True)), [], s)

    def test_invalid_plan_status(self):
        self.assertIn("invalid plan status 'Done'", vp.validate(plan_text(status="Done")))

    def test_needs_todos(self):
        text = plan_text().split("## Todo")[0] + "## Todo\n"
        self.assertIn("no todos ('- [ ] step') in '## Todo'", vp.validate(text))

    def test_missing_section_and_status(self):
        text = plan_text().replace("## Goal\n", "").replace("- Status: Planned (unverified)\n", "")
        errors = vp.validate(text)
        self.assertIn("missing section '## Goal'", errors)
        self.assertIn("missing plan field '- Status:'", errors)

    def test_each_todo_needs_a_change(self):
        text = plan_text(notes="\n- [ ] Logout works (src/logout.py)\n")
        self.assertIn("todo has no change (indented line below it): 'logout works (src/logout.py)'",
                      vp.validate(text))

    def test_template_block_format(self):
        todos = ("## Todo\n\n---\n\n- [ ] **Users log in** (src/login.py)\n  - Add a check.\n  - Add a form.\n\n---\n\n"
                 "- [ ] **Session lasts 1 day** (src/session.py)\n  - Store expiry.\n\n---\n")
        self.assertEqual(vp.validate(plan_text().split("## Todo")[0] + todos), [])

    def test_questions_and_blockers_allowed_at_end(self):
        text = plan_text(notes="\n## Questions\n1. SSO too?\n\n## Blockers\n- No test key\n")
        self.assertEqual(vp.validate(text), [])

    def test_duplicate_todos(self):
        text = plan_text(notes="- [ ] Session lasts 1 day (src/session.py)\n\n  Again.\n")
        self.assertIn("duplicate todos in '## Todo' (todos must not overlap)", vp.validate(text))

    def test_built_plan_needs_all_todos_ticked(self):
        self.assertIn("plan is Built but some todos are unchecked", vp.validate(plan_text("Built")))
        self.assertEqual(vp.validate(plan_text("Built", done=True)), [])

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
