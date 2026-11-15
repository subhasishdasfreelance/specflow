#!/usr/bin/env python3
"""PreToolUse: allow or deny a tool call based on this session's workflow mode.

Any internal error blocks the call (exit 2 = fail closed).
"""
import json
import sys

from workflow_state import COMMANDS, load, project_root, read_input

FILE_TOOLS = {"Write", "Edit", "MultiEdit", "NotebookEdit"}


def decide(data):
    state = load(data.get("session_id"))
    mode, args = state["mode"], state.get("args", "")
    tool = data.get("tool_name")
    ti = data.get("tool_input") or {}
    cwd = data.get("cwd") or str(project_root())
    if tool == "Skill":
        name = str(ti.get("skill") or ti.get("command") or "").lstrip("/")
        return f"/{name} can only be invoked by the user." if name in COMMANDS else None
    if tool in FILE_TOOLS:
        from workflow_policy import file_decision
        return file_decision(mode, args, tool, ti, cwd)
    if tool == "Bash":
        from workflow_bash import bash_decision
        return bash_decision(mode, args, str(ti.get("command") or ""), cwd)
    if tool == "PowerShell":
        return "PowerShell is not supported by the workflow hooks; use Bash."
    return None


def main():
    try:
        reason = decide(read_input())
    except Exception as exc:  # fail closed
        print(f"Workflow hook error ({type(exc).__name__}); call blocked.", file=sys.stderr)
        sys.exit(2)
    if reason:
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason}}))


if __name__ == "__main__":
    main()
