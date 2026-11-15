#!/usr/bin/env python3
"""Validate tickets in docs/tickets/ (one plan per branch). Read-only.

Usage: python3 .claude/scripts/validate_plan.py [ticket.md ...]
No arguments = validate every docs/tickets/**/*.md. Exit 1 on any error.
"""
import re
import sys
from pathlib import Path

STATUSES = ["Pending", "Planned", "Building", "Built", "Verified", "Human verified", "Blocked"]
DONE = {"Built", "Verified", "Human verified"}
SECTIONS = ["User story", "Requirements", "Approach", "Out of scope", "Tasks",
            "Acceptance criteria", "Risks", "Open questions", "Verification", "History"]
PLAN_FIELDS = ["Status", "Branch", "Base"]
TASK_FIELDS = ["Status", "Requirements", "Depends on", "Files", "Done when", "Verify"]

STATUS_RE = re.compile(r"^\s*-\s*Status:\s*(.+?)\s*$", re.M)
FIELD_RE = re.compile(r"^\s*-\s*([A-Za-z ]+):\s*(.*?)\s*$")
TASK_RE = re.compile(r"^###\s+(TASK-\d{3}):\s*(.*)$")
REQ_RE = re.compile(r"\b((?:FR|NFR|BR)-\d{3})\b")


def status_counts(text):
    """Count every '- Status: X' line, by value."""
    counts = {}
    for value in STATUS_RE.findall(text):
        counts[value] = counts.get(value, 0) + 1
    return counts


def parse(text):
    """Return {'fields', 'sections', 'tasks', 'requirements'} for a plan."""
    plan = {"fields": {}, "sections": [], "tasks": [], "requirements": set()}
    section, task = None, None
    for line in text.splitlines():
        if line.startswith("## "):
            section, task = line[3:].strip(), None
            plan["sections"].append(section)
            continue
        m = TASK_RE.match(line)
        if m and section == "Tasks":
            task = {"id": m.group(1), "title": m.group(2).strip(), "fields": {}}
            plan["tasks"].append(task)
            continue
        f = FIELD_RE.match(line)
        if section is None and f:
            plan["fields"].setdefault(f.group(1).strip(), f.group(2))
        elif task and f:
            task["fields"].setdefault(f.group(1).strip(), f.group(2))
        elif section == "Requirements":
            m = re.match(r"^\s*-\s*((?:FR|NFR|BR)-\d{3}):", line)
            if m:
                plan["requirements"].add(m.group(1))
    return plan


def plan_status(text):
    return parse(text)["fields"].get("Status")


def validate(text, branch=None):
    """Return a list of error strings (empty = valid)."""
    errors = []
    plan = parse(text)
    if branch and plan["fields"].get("Branch") not in (None, "", branch):
        errors.append(f"Branch is '{plan['fields']['Branch']}' but the file is for '{branch}'")
    for name in PLAN_FIELDS:
        if not plan["fields"].get(name):
            errors.append(f"missing plan field '- {name}:'")
    status = plan["fields"].get("Status")
    if status and status not in STATUSES:
        errors.append(f"invalid plan status '{status}'")
    for name in SECTIONS:
        if name not in plan["sections"]:
            errors.append(f"missing section '## {name}'")
    if not plan["requirements"]:
        errors.append("no requirements (FR-/NFR-/BR-###) in '## Requirements'")
    if not plan["tasks"]:
        errors.append("no tasks ('### TASK-001: Title') in '## Tasks'")

    ids = [t["id"] for t in plan["tasks"]]
    for tid in sorted({i for i in ids if ids.count(i) > 1}):
        errors.append(f"duplicate task id {tid}")
    for t in plan["tasks"]:
        tf, tid = t["fields"], t["id"]
        if not t["title"]:
            errors.append(f"{tid}: missing title")
        for name in TASK_FIELDS:
            if not tf.get(name):
                errors.append(f"{tid}: missing '- {name}:'")
        if tf.get("Status") and tf["Status"] not in STATUSES:
            errors.append(f"{tid}: invalid status '{tf['Status']}'")
        refs = REQ_RE.findall(tf.get("Requirements", ""))
        if tf.get("Requirements") and not refs:
            errors.append(f"{tid}: no requirement IDs listed")
        for ref in refs:
            if ref not in plan["requirements"]:
                errors.append(f"{tid}: unknown requirement {ref}")
        for dep in re.findall(r"TASK-\d{3}", tf.get("Depends on", "")):
            if dep not in ids:
                errors.append(f"{tid}: unknown dependency {dep}")
            if dep == tid:
                errors.append(f"{tid}: depends on itself")

    if status in DONE:
        for t in plan["tasks"]:
            if t["fields"].get("Status") not in DONE:
                errors.append(f"plan is {status} but {t['id']} is {t['fields'].get('Status')}")
    return errors


def tickets_dir():
    return Path(__file__).resolve().parents[2] / "docs" / "tickets"


def ticket_files():
    return sorted(p for p in tickets_dir().rglob("*.md") if not p.name.startswith("_"))


def branch_of(path):
    """docs/tickets/feature/login.md -> 'feature/login' (None if outside docs/tickets)."""
    try:
        return path.resolve().relative_to(tickets_dir().resolve()).with_suffix("").as_posix()
    except ValueError:
        return None


def main(argv):
    files = [Path(a) for a in argv] or ticket_files()
    if not files:
        print("No tickets found in docs/tickets/ (nothing to validate).")
        return 0
    failed = False
    for path in files:
        if not path.is_file():
            print(f"FAIL {path}: file not found")
            failed = True
            continue
        errors = validate(path.read_text(encoding="utf-8"), branch_of(path))
        print(f"{'FAIL' if errors else 'OK  '} {path}")
        for e in errors:
            print(f"  - {e}")
        failed = failed or bool(errors)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
