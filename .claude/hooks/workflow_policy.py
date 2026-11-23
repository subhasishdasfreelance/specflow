"""File-write policy: who may write which path in which mode.

Returns a deny reason (str) or None when allowed.
"""
import os
import re
import sys
import tempfile
from pathlib import Path

from workflow_state import project_root

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import validate_plan as vp  # noqa: E402

# Allowed (from, to) status changes for /build and /verify. /plan is handled in plan_status_error.
# Only the user removes a note in brackets, so no rule ever removes one.
RULES = {
    "build": {("Planned", "Building"), ("Building", "Built")},
    "verify": {("Built", vp.CLAUDE_VERIFIED)},
}
FREE_LINE = re.compile(r"^\s*-\s*Status:")
TICKED = re.compile(r"^(\s*-\s*)\[[xX]\]")
READ_ONLY_MSG = ("{mode} mode: application files are read-only. "
                 "Use /vibe for ad-hoc changes, or /plan then /build.")


def resolve(path, cwd):
    p = os.path.expanduser(str(path))
    if not os.path.isabs(p):
        p = os.path.join(cwd or str(project_root()), p)
    return os.path.realpath(p)


def _scratch_roots():
    return [os.path.realpath(tempfile.gettempdir()),
            os.path.realpath(os.path.expanduser("~/.claude/projects"))]


def _inside(path, root):
    return path == root or path.startswith(root + os.sep)


def classify(abspath):
    """root | outside | scratch | protected | prd | plan | source (plan = a ticket)"""
    root = str(project_root())
    if not _inside(abspath, root):
        return "scratch" if any(_inside(abspath, s) for s in _scratch_roots()) else "outside"
    rel = os.path.relpath(abspath, root).replace(os.sep, "/")
    if rel == ".":
        return "root"
    if rel.split("/")[0] in (".claude", ".git") or rel == "CLAUDE.md":
        return "protected"
    if rel == "docs/PRD.md":
        return "prd"
    if rel.startswith("tickets/"):
        return "plan"
    return "source"


def contains_protected(abspath):
    """True if deleting/moving abspath would take protected files with it."""
    root = project_root()
    targets = [root / ".claude", root / ".git", root / "CLAUDE.md", root / "docs" / "PRD.md",
               root / "tickets"]
    return any(_inside(str(t), abspath) for t in targets)


def has_conflict_markers(path):
    try:
        text = Path(path).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False
    return bool(re.search(r"^<{7}( |$)", text, re.M))


def active_build():
    """True when some plan is 'Building' (only reachable from an approved plan)."""
    for p in vp.ticket_files():
        try:
            if vp.plan_status(p.read_text(encoding="utf-8")) == "Building":
                return True
        except OSError:
            pass
    return False


def source_write(mode):
    if mode == "vibe":
        return None
    if mode == "build":
        return None if active_build() else (
            "/build: no plan is 'Building'. Set a Planned plan to Building first.")
    return READ_ONLY_MSG.format(mode=mode)


def file_decision(mode, args, tool, ti, cwd):
    raw = ti.get("file_path") or ti.get("notebook_path")
    if not raw:
        return "Workflow hook: no file path given."
    path = resolve(raw, cwd)
    kind = classify(path)
    if kind == "scratch":
        return None
    if kind in ("outside", "root"):
        return "Writes outside the project are not allowed."
    if kind == "protected":
        return "Workflow config, hooks and state (.claude/, .git/, CLAUDE.md) are protected. Edit them manually."
    if mode == "resolve":
        return None if has_conflict_markers(path) else (
            "/resolve-conflict may only edit files that still contain conflict markers.")
    if kind == "prd":
        return None if mode == "prd" else "docs/PRD.md changes only through /prd."
    if kind == "plan":
        return plan_decision(mode, args, tool, ti, path)
    return source_write(mode)


def simulate(tool, ti, old):
    """New file text after the edit, or None if it cannot be predicted."""
    if tool == "Write":
        return ti.get("content", "")
    edits = ti.get("edits") if tool == "MultiEdit" else [ti] if tool == "Edit" else None
    if edits is None:
        return None
    text = old
    for e in edits:
        a, b = e.get("old_string", ""), e.get("new_string", "")
        if a:
            text = text.replace(a, b) if e.get("replace_all") else text.replace(a, b, 1)
    return text


def split_blockers(text):
    """(plan text without the '## Blockers' section, that section's lines)."""
    rest, blockers, inside = [], [], False
    for line in text.splitlines():
        if line.startswith("## "):
            inside = line.strip() == "## Blockers"
        (blockers if inside else rest).append(line.rstrip())
    while blockers and not blockers[-1]:
        blockers.pop()
    return "\n".join(rest), blockers


def normalize(text):
    """Plan text minus the parts status updates may change (Status line, ticks)."""
    out = []
    for line in text.splitlines():
        if not FREE_LINE.match(line):
            out.append(TICKED.sub(r"\1[ ]", line.rstrip()))
    return "\n".join(out).strip()


def plan_status_error(old_status, new_status, is_new):
    """/plan: a new plan starts unverified; changing an existing one marks it revised."""
    if is_new:
        ok = new_status == vp.UNVERIFIED
    else:
        ok = new_status == vp.REVISED or new_status == old_status == vp.UNVERIFIED
    if ok:
        return None
    want = vp.UNVERIFIED if is_new else vp.REVISED
    return f"/plan: status must be '{want}', not '{new_status}'."


def plan_decision(mode, args, tool, ti, path):
    if mode not in ("plan", *RULES):
        return "Tickets change only through /plan (statuses via /build, /verify)."
    try:
        old = Path(path).read_text(encoding="utf-8")
    except FileNotFoundError:
        old = ""
    new = simulate(tool, ti, old)
    if new is None:
        return "Plans must be changed with Write or Edit."
    a = vp.plan_status(old)
    b = vp.plan_status(new)
    if mode == "plan":
        return plan_status_error(a, b, not old)
    if not old:
        return "Only /plan can create a plan."
    old_rest, old_blockers = split_blockers(old)
    new_rest, new_blockers = split_blockers(new)
    if normalize(old_rest) != normalize(new_rest) or new_blockers[:len(old_blockers)] != old_blockers:
        return f"/{mode} may only change the Status line, todo ticks and add to '## Blockers'."
    if a != b and (a, b) not in RULES[mode]:
        return f"/{mode}: status {a} -> {b} is not allowed."
    return None
