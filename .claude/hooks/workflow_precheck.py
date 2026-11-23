"""Check a workflow command before Claude runs it. Plain Python, no AI, no tokens.

precheck(command, args) returns a one-line reason to refuse, or None.
"""
import re
import subprocess
import sys
from pathlib import Path

from workflow_state import project_root

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import validate_plan as vp  # noqa: E402

DEFAULT_BRANCHES = ("main", "master")


def current_branch():
    result = subprocess.run(["git", "branch", "--show-current"], capture_output=True, text=True,
                            cwd=project_root())
    return result.stdout.strip()


def branch_pattern():
    """The `branch-pattern:` line of the /plan skill."""
    skill = project_root() / ".claude" / "skills" / "plan" / "SKILL.md"
    match = re.search(r"^branch-pattern:\s*(\S+)\s*$", skill.read_text(encoding="utf-8"), re.M)
    return match.group(1)


def ticket_text(branch):
    path = vp.tickets_dir() / f"{branch}.md"
    return path.read_text(encoding="utf-8") if path.is_file() else None


def precheck(command, args):
    branch = current_branch()
    if command == "plan":
        pattern = branch_pattern()
        if branch in DEFAULT_BRANCHES or not re.fullmatch(pattern, branch):
            return (f"/plan: branch '{branch}' doesn't match {pattern}. "
                    "Switch to a branch like feature/<ticket-id> (format: branch-pattern in plan/SKILL.md).")
        return None
    text = ticket_text(branch)
    if command == "build":
        if text is None:
            return f"/build: no plan for '{branch}'. Run /plan first."
        status = vp.plan_status(text)
        if status not in ("Planned", "Building"):
            if status and "(" in status:
                return "/build: plan not approved yet. Delete the note in brackets from Status."
            return f"/build: plan is '{status}'; it must be 'Planned'."
        if set(vp.OPEN_SECTIONS) & set(vp.parse(text)["sections"]):
            return "/build: answer the '## Questions' / '## Blockers' in the plan, then run /plan."
    if command == "verify":
        words = args.split()
        plan_mode = len(words) == 1 and "://" not in words[0] and text is not None
        if plan_mode and vp.plan_status(text) not in vp.DONE:
            return f"/verify: plan is '{vp.plan_status(text)}'; run /build until it is 'Built'."
    return None
