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


def plan_text(status="Pending", t1="Pending", t2="Pending", approach="Use session middleware."):
    return f"""# feature/login: Login

- Status: {status}
- Branch: feature/login
- Base: main
- Updated: 2026-11-15

## User story
As a user I want to log in so that I can see my data.

## Requirements
- FR-001: Users log in with email and password.
- NFR-001: Login responds within 1s.

## Approach
{approach}

## Out of scope
SSO.

## Tasks

### TASK-001: Login form
- Status: {t1}
- Requirements: FR-001
- Depends on: none
- Files: src/login.py
- Done when: form posts credentials
- Verify: unit test

### TASK-002: Session
- Status: {t2}
- Requirements: FR-001, NFR-001
- Depends on: TASK-001
- Files: src/session.py
- Done when: session created
- Verify: unit test

## Acceptance criteria
- AC-1: valid credentials log in.

## Risks
None.

## Open questions
None.

## Verification
Not run.

## History
- 2026-11-15: Created.
"""


class HookTest(unittest.TestCase):
    def setUp(self):
        self.root = Path(os.path.realpath(tempfile.mkdtemp(prefix="wf-")))
        for sub in ("hooks", "scripts"):
            shutil.copytree(REPO / ".claude" / sub, self.root / ".claude" / sub)
        (self.root / "docs" / "tickets").mkdir(parents=True)
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
        self.run_hook("prompt_expansion", {
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
