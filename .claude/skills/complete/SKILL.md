---
name: complete
description: Mark a verified ticket as Human verified, commit, push and open a PR.
disable-model-invocation: true
argument-hint: "<base-branch>"
---

Args: `$ARGUMENTS`. Ticket: `tickets/<current-branch>.md`. Running this means the user has checked the work by hand.

**Stop if:**
- no base branch was given (ask "Run `/complete <branch>`")
- the ticket isn't `Verified`, or you're on the base branch
- `git status` shows unrelated or secret-looking files (list them)

**Steps:**
1. Ticket → `Human verified`. Validate.
2. `git add -A`, then `git commit -F <tmpfile>`. Message: `<branch>: <Goal>`.
3. `git push -u origin <branch>`. If it fails, report and stop.
4. `gh pr create --base <base> --head <branch> --title "<branch>: <Goal>" --body-file <tmpfile>`. Body: a one-line summary and the ticket path.

Reply with the PR URL, or with what failed. Never force-push or merge.
