#!/usr/bin/env python3
"""Print a GitHub link that opens a pre-filled PR from the current branch. Read-only.

Usage: python3 .claude/scripts/pr_link.py <target-branch>
The PR body is the Goal of tickets/<branch>.md, if that ticket exists in the new structure.
"""
import re
import subprocess
import sys
from urllib.parse import quote

from validate_plan import SECTION_RE, is_new_structure, tickets_dir


def git(*args):
    return subprocess.run(["git", *args], capture_output=True, text=True, check=True).stdout.strip()


def repo_path(remote_url):
    """'owner/repo' from an ssh (host aliases like github.com-work too) or https GitHub URL, or None."""
    match = re.search(r"github\.com[^:/]*[:/](.+?)(?:\.git)?/?$", remote_url)
    return match.group(1) if match else None


def goal(ticket_text):
    if not is_new_structure(ticket_text):
        return ""
    lines, inside = [], False
    for line in ticket_text.splitlines():
        if SECTION_RE.match(line):
            inside = line.startswith("Goal:")
        elif inside and line.strip():
            lines.append(line.strip())
    return " ".join(lines)


def link(repo, target, branch, body):
    url = f"https://github.com/{repo}/compare/{target}...{branch}?expand=1"
    return url + (f"&body={quote(body)}" if body else "")


def main(argv):
    if len(argv) != 1:
        print("Usage: python3 .claude/scripts/pr_link.py <target-branch>")
        return 1
    repo = repo_path(git("remote", "get-url", "origin"))
    if not repo:
        print("origin is not a GitHub remote.")
        return 1
    branch = git("rev-parse", "--abbrev-ref", "HEAD")
    ticket = tickets_dir() / f"{branch}.md"
    body = goal(ticket.read_text(encoding="utf-8")) if ticket.is_file() else ""
    print(link(repo, argv[0], branch, body))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
