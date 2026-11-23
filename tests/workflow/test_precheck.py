import json
import subprocess
import unittest

from helpers import HookTest, plan_text

PLAN = "tickets/feature/login.md"


class PrecheckTest(HookTest):
    def refused(self, name, args=""):
        """The block reason the expansion hook prints, or None if the command may run."""
        out = self.expand(name, args).stdout.strip()
        return json.loads(out)["reason"] if out else None

    def switch(self, branch):
        subprocess.run(["git", "checkout", "-q", "-b", branch], cwd=self.root, check=True)

    def test_plan_needs_a_proper_branch(self):
        self.assertIsNone(self.refused("plan"))
        for branch in ["main", "login", "feature/a/b"]:
            with self.subTest(branch):
                self.switch(branch)
                self.assertIn("doesn't match", self.refused("plan"))
        self.switch("bug/ABC-12")
        self.assertIsNone(self.refused("plan"))

    def test_branch_pattern_is_read_from_plan_skill(self):
        skill = self.root / ".claude/skills/plan/SKILL.md"
        skill.write_text(skill.read_text().replace("^(feature|bug)/[A-Za-z0-9-]+$", "^[A-Z]+-[0-9]+$"))
        self.assertIsNotNone(self.refused("plan"))
        self.switch("JIRA-123")
        self.assertIsNone(self.refused("plan"))

    def test_build_needs_an_approved_plan(self):
        self.assertIn("no plan", self.refused("build"))
        for status in ["Planned (unverified)", "Planned (revised, unverified)"]:
            self.put(PLAN, plan_text(status))
            self.assertIn("note in brackets", self.refused("build"))
        self.put(PLAN, plan_text("Built", done=True))
        self.assertIn("must be 'Planned'", self.refused("build"))
        for status in ["Planned", "Building"]:
            self.put(PLAN, plan_text(status))
            self.assertIsNone(self.refused("build"))

    def test_build_refused_with_questions_or_blockers(self):
        for section in ["## Questions\n1. SSO too?\n", "## Blockers\n- No test key\n"]:
            self.put(PLAN, plan_text("Planned", notes="\n" + section))
            self.assertIn("## Questions", self.refused("build"))

    def test_verify_plan_needs_built(self):
        self.put(PLAN, plan_text("Building"))
        self.assertIn("'Built'", self.refused("verify", "main"))
        self.assertIsNone(self.refused("verify", "main Users can log in"))  # pasted requirement
        self.assertIsNone(self.refused("verify", "https://github.com/acme/app/pull/7"))
        for status in ["Built", "Verified (not human-verified)", "Verified"]:
            self.put(PLAN, plan_text(status, done=True))
            self.assertIsNone(self.refused("verify", "main"))

    def test_refused_command_grants_no_mode(self):
        self.put(PLAN, plan_text())
        self.slash("build")
        self.assertDenied(self.write("src/login.py"))


if __name__ == "__main__":
    unittest.main()
