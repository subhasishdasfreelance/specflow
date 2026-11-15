#!/usr/bin/env python3
"""Validate tickets in tickets/ (one plan per branch). Read-only.

Usage: python3 .claude/scripts/validate_plan.py [ticket.md ...]
No arguments = validate every tickets/**/*.md. Exit 1 on any error.
"""
import re
import sys
from pathlib import Path

STATUSES = ["Pending", "Planned", "Building", "Built", "Verified", "Human verified", "Blocked"]
DONE = {"Built", "Verified", "Human verified"}
SECTIONS = ["Goal", "Todo", "Changes"]
PLAN_FIELDS = ["Status"]

FIELD_RE = re.compile(r"^\s*-\s*([A-Za-z ]+):\s*(.*?)\s*$")
TODO_RE = re.compile(r"^\s*-\s*\[([ xX])\]\s*(\S.*?)\s*$")
CHANGE_RE = re.compile(r"^\s*\d+\.\s+(\S.*?)\s*$")


def parse(text):
    """Return {'fields', 'sections', 'changes', 'todos'} for a plan. todos = list of (done, text)."""
    plan = {"fields": {}, "sections": [], "changes": [], "todos": []}
    section = None
    for line in text.splitlines():
        if line.startswith("## "):
            section = line[3:].strip()
            plan["sections"].append(section)
            continue
        f = FIELD_RE.match(line)
        if section is None and f:
            plan["fields"].setdefault(f.group(1).strip(), f.group(2))
        elif section == "Changes" and CHANGE_RE.match(line):
            plan["changes"].append(CHANGE_RE.match(line).group(1).lower())
        elif section == "Todo" and TODO_RE.match(line):
            done, todo = TODO_RE.match(line).groups()
            plan["todos"].append((done != " ", todo.lower()))
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
    if "Changes" in plan["sections"]:
        if plan["sections"][-1] != "Changes":
            errors.append("'## Changes' must be the last section")
        if not plan["changes"]:
            errors.append("no changes ('1. change') in '## Changes'")
        if len(set(plan["changes"])) < len(plan["changes"]):
            errors.append("duplicate changes in '## Changes' (changes must not overlap)")
    todos = [todo for _, todo in plan["todos"]]
    if not todos:
        errors.append("no todos ('- [ ] step') in '## Todo'")
    if len(set(todos)) < len(todos):
        errors.append("duplicate todos in '## Todo' (todos must not overlap)")
    if status in DONE and not all(done for done, _ in plan["todos"]):
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
