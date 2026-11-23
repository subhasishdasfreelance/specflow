#!/usr/bin/env python3
"""Validate tickets in tickets/ (one plan per branch). Read-only.

Usage: python3 .claude/scripts/validate_plan.py [ticket.md ...]
No arguments = validate every tickets/**/*.md in the new structure. Exit 1 on any error.

New structure: a "Status:" line, "Goal:" and "Todo:" headings, and one line per item
starting with a mark, each with numbered changes indented below it.
Old-structure tickets (no line starting with "Status:") are skipped.
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
TODO, TICKED = "📝", "✅"
OPEN_MARKS = {"❓", "⛔"}  # while any is left, /build is refused

STATUS_RE = re.compile(r"^Status:\s*(.*?)\s*$", re.M)
SECTION_RE = re.compile(r"^(Goal|Todo):\s*$")
ITEM_RE = re.compile(r"^(📝|✅|❓|⚠️?|⛔|❌)\s*(.*?)\s*$")
CHANGE_RE = re.compile(r"^\s+\d+\.\s+\S")  # an indented, numbered line below an item


def is_new_structure(text):
    return bool(STATUS_RE.search(text))


def parse(text):
    """Return {'status', 'sections', 'items'}. items = list of [mark, text, has_change]."""
    match = STATUS_RE.search(text)
    plan = {"status": match.group(1) if match else None, "sections": [], "items": []}
    section = None
    for line in text.splitlines():
        if SECTION_RE.match(line):
            section = SECTION_RE.match(line).group(1)
            plan["sections"].append(section)
        elif section == "Todo" and ITEM_RE.match(line):
            mark, item = ITEM_RE.match(line).groups()
            plan["items"].append([mark.rstrip("\ufe0f"), item, False])
        elif section == "Todo" and plan["items"] and CHANGE_RE.match(line):
            plan["items"][-1][2] = True
    return plan


def plan_status(text):
    return parse(text)["status"]


def open_items(text):
    """The ❓ and ⛔ items, as 'mark text' lines."""
    return [f"{mark} {item}" for mark, item, _ in parse(text)["items"] if mark in OPEN_MARKS]


def validate(text):
    """Return a list of error strings (empty = valid)."""
    errors = []
    plan = parse(text)
    status = plan["status"]
    if not status:
        errors.append("missing 'Status:' line")
    elif status not in STATUSES:
        errors.append(f"invalid plan status '{status}'")
    for name in SECTIONS:
        if name not in plan["sections"]:
            errors.append(f"missing heading '{name}:'")
    items = [item.lower() for _, item, _ in plan["items"]]
    if not any(mark in (TODO, TICKED) for mark, _, _ in plan["items"]):
        errors.append(f"no {TODO} or {TICKED} item under 'Todo:'")
    if len(set(items)) < len(items):
        errors.append("duplicate items under 'Todo:' (items must not overlap)")
    for mark, item, has_change in plan["items"]:
        if not has_change:
            errors.append(f"item has no numbered change below it: '{mark} {item}'")
        if "`" in item:
            errors.append(f"item uses backticks (plain words only): '{mark} {item}'")
    if status in DONE and any(mark == TODO for mark, _, _ in plan["items"]):
        errors.append(f"plan is {status} but a {TODO} todo remains")
    return errors


def tickets_dir():
    return Path(__file__).resolve().parents[2] / "tickets"


def ticket_files():
    return sorted(p for p in tickets_dir().rglob("*.md")
                  if not p.name.startswith("_") and is_new_structure(p.read_text(encoding="utf-8")))


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
