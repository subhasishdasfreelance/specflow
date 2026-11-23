import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from helpers import OLD_PLAN, REPO, plan_text

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
        text = plan_text().split("Todo:")[0] + "Todo:\n❓ SSO too?\n  1. Or email only.\n"
        self.assertIn("no 📝 or ✅ item under 'Todo:'", vp.validate(text))

    def test_missing_heading_and_status(self):
        text = plan_text().replace("Goal:\n", "").replace("Status: Planned (unverified)\n", "")
        errors = vp.validate(text)
        self.assertIn("missing heading 'Goal:'", errors)
        self.assertIn("missing 'Status:' line", errors)

    def test_each_item_needs_a_numbered_change(self):
        for notes in ["📝 Logout works (src/logout.py)\n", "❓ SSO too?\n  Not numbered.\n"]:
            with self.subTest(notes):
                self.assertTrue(any("no numbered change" in e for e in vp.validate(plan_text(notes=notes))))

    def test_every_mark_accepted(self):
        notes = "".join(f"{m} Item {i}\n  1. Detail.\n" for i, m in enumerate(["❓", "⚠️", "⚠", "⛔", "❌"]))
        self.assertEqual(vp.validate(plan_text(notes=notes)), [])
        self.assertEqual(vp.open_items(plan_text(notes=notes)), ["❓ Item 0", "⛔ Item 3"])
        self.assertEqual(vp.open_items(plan_text()), [])

    def test_backticks_rejected(self):
        text = plan_text(notes="📝 Add `logout` (src/logout.py)\n  1. Add it.\n")
        self.assertTrue(any("backticks" in e for e in vp.validate(text)))

    def test_blank_lines_around_changes_allowed(self):
        text = plan_text().replace("(src/login.py)\n", "(src/login.py)\n\n").replace("login.py.\n", "login.py.\n\n\n")
        self.assertEqual(vp.validate(text), [])

    def test_template_is_valid(self):
        template = (REPO / ".claude/skills/plan/plan-template.md").read_text()
        self.assertEqual(vp.validate(template), [])

    def test_duplicate_items(self):
        text = plan_text(notes="📝 Session lasts 1 day (src/session.py)\n  1. Again.\n")
        self.assertIn("duplicate items under 'Todo:' (items must not overlap)", vp.validate(text))

    def test_built_plan_needs_all_todos_done(self):
        self.assertIn("plan is Built but a 📝 todo remains", vp.validate(plan_text("Built")))
        notes = "⚠️ Slow\n  1. Watch it.\n❌ SSO\n  1. Later.\n"
        self.assertEqual(vp.validate(plan_text("Built", done=True, notes=notes)), [])

    def test_ticket_files_skip_old_structure(self):
        with tempfile.TemporaryDirectory() as d:
            Path(d, "new.md").write_text(plan_text())
            Path(d, "old.md").write_text(OLD_PLAN)
            with mock.patch.object(vp, "tickets_dir", return_value=Path(d)):
                self.assertEqual([p.name for p in vp.ticket_files()], ["new.md"])

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
