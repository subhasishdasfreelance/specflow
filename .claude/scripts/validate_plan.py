#!/usr/bin/env python3
"""Validate tickets in tickets/ (one plan per branch). Read-only.

Usage: python3 .claude/scripts/validate_plan.py [ticket.md ...]
No arguments = validate every tickets/**/*.md. Exit 1 on any error.
"""
import re
import sys
from pathlib import Path

# A note in brackets means "waiting for the user"; only the user deletes it.
UNVERIFIED = "Planned (unverified)"
REVISED = "Planned (revised, unverified)"
CLAUDE_VERIFIED = "Verified (not human-verified)"
STATUSES = [UNVERIFIED, REVISED, "Planned", "Building", "Built", CLAUDE_VERIFIED, "Verified"]
DONE = {"Built", CLAUDE_VERIFIED, "Verified"}
SECTIONS = ["Goal", "Todo"]
OPEN_SECTIONS = ["Questions", "Blockers"]  # while either exists, /build is refused
PLAN_FIELDS = ["Status"]

FIELD_RE = re.compile(r"^\s*-\s*([A-Za-z ]+):\s*(.*?)\s*$")
TODO_RE = re.compile(r"^\s*-\s*\[([ xX])\]\s*(\S.*?)\s*$")
CHANGE_RE = re.compile(r"^\s+\S")  # an indented line below a todo


def parse(text):
    """Return {'fields', 'sections', 'todos'} for a plan. todos = list of (done, text, has_change)."""
    plan = {"fields": {}, "sections": [], "todos": []}
    section = None
    for line in text.splitlines():
        if line.startswith("## "):
            section = line[3:].strip()
            plan["sections"].append(section)
            continue
        f = FIELD_RE.match(line)
        if section is None and f:
            plan["fields"].setdefault(f.group(1).strip(), f.group(2))
        elif section == "Todo" and TODO_RE.match(line):
            done, todo = TODO_RE.match(line).groups()
            plan["todos"].append((done != " ", todo.lower(), False))
        elif section == "Todo" and plan["todos"] and CHANGE_RE.match(line):
            done, todo, _ = plan["todos"][-1]
            plan["todos"][-1] = (done, todo, True)
    return plan


def plan_status(text):
    return parse(text)["fields"].get("Status")


def validate(text):
    """Return a list of error strings (empty = valid)."""
    errors = []
    plan = parse(text)
    for name in PLAN_FIELDS:
        if not plan["fields"].get(name):
            errors.append(f"missing plan field '- {name}:'")
    status = plan["fields"].get("Status")
    if status and status not in STATUSES:
        errors.append(f"invalid plan status '{status}'")
    for name in SECTIONS:
        if name not in plan["sections"]:
            errors.append(f"missing section '## {name}'")
    todos = [todo for _, todo, _ in plan["todos"]]
    if not todos:
        errors.append("no todos ('- [ ] step') in '## Todo'")
    if len(set(todos)) < len(todos):
        errors.append("duplicate todos in '## Todo' (todos must not overlap)")
    for _, todo, has_change in plan["todos"]:
        if not has_change:
            errors.append(f"todo has no change (indented line below it): '{todo}'")
    if status in DONE and not all(done for done, _, _ in plan["todos"]):
        errors.append(f"plan is {status} but some todos are unchecked")
    return errors


def tickets_dir():
    return Path(__file__).resolve().parents[2] / "tickets"


def ticket_files():
    return sorted(p for p in tickets_dir().rglob("*.md") if not p.name.startswith("_"))


def main(argv):
    files = [Path(a) for a in argv] or ticket_files()
    if not files:
        print("No tickets found in tickets/ (nothing to validate).")
        return 0
    failed = False
    for path in files:
        if not path.is_file():
            print(f"FAIL {path}: file not found")
            failed = True
            continue
        errors = validate(path.read_text(encoding="utf-8"))
        print(f"{'FAIL' if errors else 'OK  '} {path}")
        for e in errors:
            print(f"  - {e}")
        failed = failed or bool(errors)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
