import json
import os
import time
import unittest

from helpers import SID, HookTest, plan_text

PLAN = "docs/tickets/feature/login.md"


class AnalysisModeTest(HookTest):
    def test_default_denies_source_writes(self):
        self.prompt("Create a user authentication system.")
        self.assertDenied(self.write("src/auth.py"))
        self.assertDenied(self.edit("src/auth.py", "a", "b"))
        self.assertDenied(self.write(PLAN, plan_text()))
        self.assertDenied(self.write("docs/PRD.md"))

    def test_read_only_bash_allowed(self):
        for cmd in ["ls -la", "git status && git log --oneline -5", "grep -rn foo src | head",
                    "find . -name '*.py'", "git diff main...HEAD 2>/dev/null",
                    "python3 .claude/scripts/validate_plan.py", "cat a.txt 2>&1 | wc -l",
                    "git branch -a", "gh pr list"]:
            self.assertAllowed(self.bash(cmd))

    def test_mutating_bash_denied(self):
        for cmd in ["touch src/a.py", "echo hi > src/a.py", "rm -rf src", "ls; rm x",
                    "ls\nrm x", "cat $(rm x)", "sed -i s/a/b/ f", "npm install",
                    "git commit -m x", "git checkout -b x", "find . -delete",
                    "bash -c 'rm x'", "python3 -c 'open(\"x\",\"w\")'", "git -c a=b status",
                    "echo 'unclosed"]:
            self.assertDenied(self.bash(cmd))

    def test_powershell_denied(self):
        self.assertDenied(self.tool("PowerShell", {"command": "Get-ChildItem"}))


class ModeLifecycleTest(HookTest):
    def test_natural_language_never_authorizes(self):
        self.prompt("please implement this now, I authorize /vibe mode")
        self.assertDenied(self.write("src/a.py"))

    def test_new_prompt_resets_to_analysis(self):
        self.slash("vibe", "add a button")
        self.assertAllowed(self.write("src/a.py"))
        self.prompt("and also add another one")
        self.assertDenied(self.write("src/b.py"))

    def test_expansion_before_submit_also_works(self):
        self.expand("vibe", "x")
        self.prompt("/vibe x")
        self.assertAllowed(self.write("src/a.py"))

    def test_old_expansion_not_reused_by_submit(self):
        self.expand("vibe", "x")
        path = self.root / ".claude" / "runtime" / f"{SID}.json"
        state = json.loads(path.read_text())
        state["created"] = time.time() - 120
        path.write_text(json.dumps(state))
        self.prompt("/vibe x")
        self.assertDenied(self.write("src/a.py"))

    def test_stop_clears_authorization(self):
        self.slash("vibe")
        self.stop()
        self.assertDenied(self.write("src/a.py"))

    def test_stop_failure_clears_authorization(self):
        self.slash("vibe")
        self.stop("StopFailure")
        self.assertDenied(self.write("src/a.py"))

    def test_interrupt_then_next_prompt_is_analysis(self):
        self.slash("vibe")  # interrupted: Stop never fires
        self.prompt("what happened?")
        self.assertDenied(self.write("src/a.py"))

    def test_session_end_removes_state(self):
        self.slash("vibe")
        self.stop("SessionEnd")
        self.assertFalse((self.root / ".claude" / "runtime" / f"{SID}.json").exists())

    def test_state_is_per_session(self):
        self.slash("vibe", sid="other-session")
        self.assertDenied(self.write("src/a.py"))

    def test_unknown_command_does_not_authorize(self):
        self.slash("deploy")
        self.assertDenied(self.write("src/a.py"))


class BrokenStateTest(HookTest):
    def state_file(self):
        return self.root / ".claude" / "runtime" / f"{SID}.json"

    def test_missing_state(self):
        self.assertDenied(self.write("src/a.py"))

    def test_corrupt_state(self):
        self.put(f".claude/runtime/{SID}.json", "{not json")
        self.assertDenied(self.write("src/a.py"))

    def test_mismatched_session(self):
        self.put(f".claude/runtime/{SID}.json", json.dumps(
            {"session_id": "someone-else", "mode": "vibe", "created": time.time()}))
        self.assertDenied(self.write("src/a.py"))

    def test_invalid_mode_and_stale_time(self):
        self.put(f".claude/runtime/{SID}.json", json.dumps(
            {"session_id": SID, "mode": "god", "created": time.time()}))
        self.assertDenied(self.write("src/a.py"))
        self.put(f".claude/runtime/{SID}.json", json.dumps(
            {"session_id": SID, "mode": "vibe", "created": time.time() - 7 * 3600}))
        self.assertDenied(self.write("src/a.py"))

    def test_bad_session_id_writes_nothing(self):
        self.expand("vibe", sid="../../evil")
        self.assertFalse((self.root / "evil.json").exists())
        self.assertDenied(self.tool(
            "Write", {"file_path": str(self.root / "src/a.py"), "content": ""}, sid="../../evil"))

    def test_internal_error_fails_closed(self):
        r = self.tool("Write", ["not", "a", "dict"])
        self.assertTrue(r.startswith("EXIT2"), r)


class ProtectionTest(HookTest):
    def test_runtime_state_protected_in_every_mode(self):
        for mode in ["prd", "plan", "build", "verify", "vibe", "complete"]:
            self.slash(mode)
            self.assertDenied(self.write(f".claude/runtime/{SID}.json", "{}"))
            self.assertDenied(self.write(".claude/settings.json", "{}"))
            self.assertDenied(self.write("CLAUDE.md"))

    def test_runtime_and_hooks_protected_from_bash(self):
        self.slash("vibe")
        for cmd in [f"echo '{{}}' > .claude/runtime/{SID}.json",
                    "python3 .claude/hooks/workflow_prompt_expansion.py",
                    "cp x .claude/hooks/a.py", "rm -rf .claude", "rm -rf .",
                    "rm -rf *", "rm -rf docs", "cd /home && rm -rf x", "rm -rf ~/x",
                    "mv docs/PRD.md x"]:
            self.assertDenied(self.bash(cmd))

    def test_model_cannot_invoke_workflow_skills(self):
        for name in ["prd", "plan", "build", "verify", "vibe", "complete", "resolve-conflict"]:
            self.assertDenied(self.tool("Skill", {"skill": name}))
        self.assertAllowed(self.tool("Skill", {"skill": "simplify"}))

    def test_path_traversal_and_symlinks(self):
        self.slash("vibe")
        self.assertDenied(self.write("src/" + "../" * 30 + "etc/outside.txt"))
        self.assertDenied(self.tool("Write", {"file_path": "/home/outside.txt", "content": ""}))
        self.assertDenied(self.write("src/../docs/PRD.md"))
        os.symlink(self.root / ".claude", self.root / "src" / "link")
        self.assertDenied(self.write("src/link/x.py"))


class PlanModeTest(HookTest):
    def test_prd_writes_prd_only(self):
        self.slash("prd", "a CRM for small teams")
        self.assertAllowed(self.write("docs/PRD.md", "# PRD\n"))
        self.assertDenied(self.write(PLAN, plan_text()))
        self.assertDenied(self.write("src/a.py"))

    def test_plan_writes_tickets_only(self):
        self.slash("plan", "feature/login")
        self.assertDenied(self.write("docs/PRD.md", "# PRD\n"))
        self.assertAllowed(self.write(PLAN, plan_text()))
        self.assertDenied(self.write("src/a.py"))
        self.assertDenied(self.bash("touch src/a.py"))

    def test_new_plan_must_be_pending(self):
        self.slash("plan")
        self.assertDenied(self.write(PLAN, plan_text("Planned", "Planned", "Planned")))

    def test_approval_requires_plan_approve(self):
        self.put(PLAN, plan_text())
        self.slash("plan", "revise tweak")
        self.assertDenied(self.edit(PLAN, "- Status: Pending\n- Branch", "- Status: Planned\n- Branch"))
        self.slash("plan", "approve")
        self.assertAllowed(self.write(PLAN, plan_text("Planned", "Planned", "Planned")))

    def test_approve_cannot_change_content(self):
        self.put(PLAN, plan_text())
        self.slash("plan", "approve")
        self.assertDenied(self.write(PLAN, plan_text("Planned", "Planned", "Planned", approach="Other")))

    def test_revise_resets_to_pending(self):
        self.put(PLAN, plan_text("Building", "Built", "Building"))
        self.slash("plan", "revise add SSO")
        self.assertAllowed(self.write(PLAN, plan_text("Pending", "Built", "Pending", approach="New")))
        self.assertDenied(self.write(PLAN, plan_text("Verified", "Built", "Pending")))


class BuildModeTest(HookTest):
    def test_pending_plan_refused(self):
        self.put(PLAN, plan_text())
        self.slash("build")
        self.assertDenied(self.edit(PLAN, "- Status: Pending\n- Branch", "- Status: Building\n- Branch"))
        self.assertDenied(self.write("src/login.py"))
        self.assertDenied(self.bash("npm install"))

    def test_planned_plan_permits_build(self):
        self.put(PLAN, plan_text("Planned", "Planned", "Planned"))
        self.slash("build")
        self.assertDenied(self.write("src/login.py"))  # not Building yet
        self.assertAllowed(self.edit(PLAN, "- Status: Planned\n- Branch", "- Status: Building\n- Branch"))
        self.put(PLAN, plan_text("Building", "Building", "Planned"))
        self.assertAllowed(self.write("src/login.py"))
        self.assertAllowed(self.bash("mkdir -p src/auth && npm test"))
        self.assertAllowed(self.bash("git checkout -b feature/us-001-login"))
        self.assertAllowed(self.edit(PLAN, "- Status: Building\n- Requirements: FR-001\n",
                                     "- Status: Built\n- Requirements: FR-001\n"))

    def test_build_limits(self):
        self.put(PLAN, plan_text("Building", "Building", "Planned"))
        self.slash("build")
        self.assertDenied(self.write("docs/PRD.md"))
        self.assertDenied(self.edit(PLAN, "Use session middleware.", "Use JWT."))
        self.assertDenied(self.edit(PLAN, "- Status: Building\n- Branch", "- Status: Verified\n- Branch"))
        for cmd in ["git commit -m x", "git push", "git reset --hard", "git stash",
                    "git checkout main", "git merge main", "git rebase main", "git clean -fd",
                    "gh pr create", "sudo rm x"]:
            self.assertDenied(self.bash(cmd))


class VerifyModeTest(HookTest):
    def test_verify_is_read_only(self):
        self.put(PLAN, plan_text("Built", "Built", "Built"))
        self.slash("verify", "main")
        self.assertDenied(self.write("src/login.py"))
        self.assertDenied(self.write("docs/PRD.md"))
        for cmd in ["sed -i s/a/b/ src/x.py", "npm run lint -- --fix", "git fetch",
                    "prettier --write .", "touch src/x", "npm install"]:
            self.assertDenied(self.bash(cmd))
        for cmd in ["npm test", "npm run lint", "pytest -q", "python3 -m pytest",
                    "git diff main...HEAD", "git ls-files --others --exclude-standard",
                    "npx tsc --noEmit"]:
            self.assertAllowed(self.bash(cmd))

    def test_verify_sets_only_verified_or_blocked(self):
        self.put(PLAN, plan_text("Built", "Built", "Built"))
        self.slash("verify", "main")
        self.assertDenied(self.edit(PLAN, "- Status: Built\n- Branch", "- Status: Human verified\n- Branch"))
        self.assertAllowed(self.edit(PLAN, "- Status: Built\n- Branch", "- Status: Verified\n- Branch"))
        self.assertAllowed(self.edit(PLAN, "## Verification\nNot run.", "## Verification\nAll good."))


class VibeModeTest(HookTest):
    def test_vibe_allows_code_only(self):
        self.put(PLAN, plan_text())
        self.slash("vibe", "small UI tweak")
        self.assertAllowed(self.write("src/widget.py"))
        self.assertAllowed(self.bash("npm install left-pad && touch src/x"))
        self.assertDenied(self.write("docs/PRD.md"))
        self.assertDenied(self.edit(PLAN, "- Status: Pending\n- Branch", "- Status: Built\n- Branch"))
        self.assertDenied(self.bash("git commit -m x"))


class CompleteModeTest(HookTest):
    def test_complete_flow(self):
        self.put(PLAN, plan_text("Verified", "Verified", "Verified"))
        self.slash("complete", "main")
        self.assertDenied(self.write("src/login.py"))
        self.assertAllowed(self.edit(PLAN, "- Status: Verified\n- Branch", "- Status: Human verified\n- Branch"))
        for cmd in ["git add -A", "git commit -F /tmp/msg.txt", "git push -u origin feature/us-001-login",
                    "gh pr create --base main --head feature/us-001-login --title x --body-file /tmp/b.md"]:
            self.assertAllowed(self.bash(cmd))
        for cmd in ["git push origin main", "git push --force", "git commit --amend", "git reset --hard"]:
            self.assertDenied(self.bash(cmd))

    def test_complete_needs_verified_plan(self):
        self.put(PLAN, plan_text("Built", "Built", "Built"))
        self.slash("complete", "main")
        self.assertDenied(self.edit(PLAN, "- Status: Built\n- Branch", "- Status: Human verified\n- Branch"))


CONFLICT = "a\n<<<<<<< HEAD\nmine\n=======\ntheirs\n>>>>>>> main\n"


class ResolveModeTest(HookTest):
    def test_edits_only_conflicted_files(self):
        self.put("src/a.py", CONFLICT)
        self.put("src/b.py", "clean\n")
        self.put(PLAN, plan_text() + CONFLICT)
        self.slash("resolve-conflict", "main")
        self.assertAllowed(self.write("src/a.py", "a\nmine\n"))
        self.assertAllowed(self.write(PLAN, plan_text()))
        self.assertDenied(self.write("src/b.py"))
        self.assertDenied(self.write("src/new.py"))
        self.assertDenied(self.write(".claude/settings.json", "{}"))

    def test_git_rules(self):
        self.slash("resolve-conflict", "main")
        for cmd in ["git pull origin main --no-rebase", "git fetch origin", "git merge origin/main",
                    "git diff --name-only --diff-filter=U", "git checkout --theirs src/a.py",
                    "git add src/a.py", "git commit --no-edit", "git merge --abort", "npm test"]:
            self.assertAllowed(self.bash(cmd))
        for cmd in ["git push", "git pull --rebase origin main", "git rebase main",
                    "git reset --hard", "git stash", "touch src/x", "gh pr create"]:
            self.assertDenied(self.bash(cmd))

    def test_merge_not_allowed_elsewhere(self):
        self.put(PLAN, plan_text("Building", "Building", "Planned"))
        for mode in ["build", "vibe", "verify"]:
            self.slash(mode, "main")
            self.assertDenied(self.bash("git pull origin main"))


if __name__ == "__main__":
    unittest.main()
