"""Shared fixtures: a throwaway project with a copy of the workflow hooks."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SID = "test-session-1"


def plan_text(status="Planned (unverified)", done=False, notes=""):
    mark = "✅" if done else "📝"
    return f"""feature/login
Status: {status}

Goal:
Users log in to see their data.

Todo:
{mark} Users log in with email and password (src/login.py)
  1. Add an email/password check in src/login.py.
{mark} Session lasts 1 day (src/session.py)
  1. Store sessions with a 1-day expiry in src/session.py.
{notes}"""


OLD_PLAN = "# feature/login\n\n- Status: Planned\n\n## Goal\nOld.\n\n## Todo\n- [ ] Old todo\n  Old change.\n"


class HookTest(unittest.TestCase):
    def setUp(self):
        self.root = Path(os.path.realpath(tempfile.mkdtemp(prefix="wf-")))
        for sub in ("hooks", "scripts", "skills"):
            shutil.copytree(REPO / ".claude" / sub, self.root / ".claude" / sub)
        subprocess.run(["git", "init", "-q", "-b", "feature/login"], cwd=self.root, check=True)
        (self.root / "tickets").mkdir()
        (self.root / "docs").mkdir()
        (self.root / "src").mkdir()
        self.env = {**os.environ, "CLAUDE_PROJECT_DIR": str(self.root)}

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def run_hook(self, name, payload):
        script = self.root / ".claude" / "hooks" / f"workflow_{name}.py"
        return subprocess.run([sys.executable, str(script)], input=json.dumps(payload),
                              capture_output=True, text=True, env=self.env, cwd=self.root)

    # --- user actions ---
    def prompt(self, text, sid=SID):
        self.run_hook("prompt_submit", {"session_id": sid, "hook_event_name": "UserPromptSubmit",
                                        "prompt": text, "cwd": str(self.root)})

    def expand(self, name, args="", sid=SID):
        return self.run_hook("prompt_expansion", {
            "session_id": sid, "hook_event_name": "UserPromptExpansion",
            "expansion_type": "slash_command", "command_name": name,
            "command_args": args, "prompt": f"/{name} {args}".strip()})

    def slash(self, name, args="", sid=SID):
        """Real order per docs diagram: UserPromptSubmit, then UserPromptExpansion."""
        self.prompt(f"/{name} {args}".strip(), sid)
        self.expand(name, args, sid)

    def stop(self, event="Stop", sid=SID):
        self.run_hook("stop", {"session_id": sid, "hook_event_name": event})

    # --- tool calls ---
    def tool(self, tool_name, tool_input, sid=SID):
        r = self.run_hook("pre_tool", {"session_id": sid, "hook_event_name": "PreToolUse",
                                       "tool_name": tool_name, "tool_input": tool_input,
                                       "cwd": str(self.root)})
        if r.returncode == 2:
            return "EXIT2:" + r.stderr
        self.assertEqual(r.returncode, 0, r.stderr)
        if not r.stdout.strip():
            return None
        out = json.loads(r.stdout)["hookSpecificOutput"]
        self.assertEqual(out["permissionDecision"], "deny")
        return out["permissionDecisionReason"]

    def write(self, rel, content="x\n"):
        return self.tool("Write", {"file_path": str(self.root / rel), "content": content})

    def edit(self, rel, old, new):
        return self.tool("Edit", {"file_path": str(self.root / rel),
                                  "old_string": old, "new_string": new})

    def bash(self, command):
        return self.tool("Bash", {"command": command})

    def put(self, rel, content):
        """Write a fixture file directly (not through the hook)."""
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def assertAllowed(self, reason):
        self.assertIsNone(reason, reason)

    def assertDenied(self, reason):
        self.assertIsNotNone(reason, "expected the call to be denied")
