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

# Allowed (from, to) status changes per mode. "*" = any previous value.
RULES = {
    "plan": {("*", "Pending"), ("*", "Blocked")},
    "build": {("Planned", "Building"), ("Building", "Built"), ("Blocked", "Building"),
              ("Planned", "Blocked"), ("Building", "Blocked")},
    # /verify adds "Claude verified"; /verify human adds "Human verified". Both, in the order done.
    "verify": {("Built", "Claude verified"), ("Built", "Human verified"),
               ("Claude verified", "Claude verified + Human verified"),
               ("Human verified", "Human verified + Claude verified"),
               ("Built", "Blocked"), ("Claude verified", "Blocked"), ("Human verified", "Blocked")},
}
FREE_LINE = re.compile(r"^\s*-\s*(Status|Updated|Blocker):")
TICKED = re.compile(r"^(\s*-\s*)\[[xX]\]")
READ_ONLY_MSG = ("{mode} mode: application files are read-only. "
                 "Use /vibe for ad-hoc changes, or approve a plan (/plan approve) and run /build.")


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
            "/build: no plan is 'Building'. Set an approved (Planned) plan to Building first.")
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


def normalize(text):
    """Plan text minus the parts status updates may change (Status/Blocker lines, ticks)."""
    out = []
    for line in text.splitlines():
        if not FREE_LINE.match(line):
            out.append(TICKED.sub(r"\1[ ]", line.rstrip()))
    return "\n".join(out).strip()


def _allowed(mode, old, new, approve):
    if new not in vp.STATUSES:
        return False
    if approve and old in (None, "Pending") and new == "Planned":
        return True
    rules = RULES.get(mode, set())
    return (old, new) in rules or ("*", new) in rules


def transition_error(mode, approve, old_text, new_text):
    a = vp.parse(old_text)["fields"].get("Status")
    b = vp.parse(new_text)["fields"].get("Status")
    if a != b and not _allowed(mode, a, b, approve):
        hint = " Approval needs '/plan approve'." if b == "Planned" else ""
        return f"/{mode}: status {a or 'new'} -> {b} is not allowed.{hint}"
    return None


def plan_decision(mode, args, tool, ti, path):
    if mode not in RULES:
        return "Tickets change only through /plan (statuses via /build, /verify)."
    try:
        old = Path(path).read_text(encoding="utf-8")
    except FileNotFoundError:
        old = ""
    new = simulate(tool, ti, old)
    if new is None:
        return "Plans must be changed with Write or Edit."
    approve = mode == "plan" and args.split()[:1] == ["approve"]
    if mode != "plan" or approve:
        if not old:
            return "Only /plan can create a plan."
        if normalize(old) != normalize(new):
            what = "/plan approve" if approve else f"/{mode}"
            return (f"{what} may only change Status/Blocker lines and todo ticks of a plan.")
    return transition_error(mode, approve, old, new)
