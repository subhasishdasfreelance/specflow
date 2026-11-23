---
name: verify
description: Review the current branch against its plan, or a PR or branch against a pasted requirement, and give a PR link.
disable-model-invocation: true
argument-hint: "<target-branch | PR link> [pasted requirement]"
---

Args: `$ARGUMENTS`. Read-only: never change code or git state (no commits, no pushes). You may edit only the ticket's `Status` line.

1. No target given: show `git branch -a` and the current branch, ask "Run `/verify <target>`", and stop.
2. Pick the mode:
   - **Plan:** only a target branch was given and `tickets/<current-branch>.md` exists. The requirement is its Goal and todos. (A hook already checked it is `Built` or verified.)
   - **PR review:** a PR link was given, or a requirement was pasted after the target. The requirement is the pasted text; if none was pasted, ask for it and stop. Never touch a ticket.
3. Read the changes. Branch: `git log <t>..HEAD`, `git diff <t>...HEAD`, `git diff --cached`, `git diff`, and untracked files (`git ls-files --others --exclude-standard`; read them directly). PR link: `gh pr view <link>` and `gh pr diff <link>`.
4. Check each todo (or each point of the requirement). Run the project's existing test, lint and build commands (on the current branch only). Review like a PR: bugs, security, missing tests, deviations, bloat. Flag every change the requirement doesn't need as `[Scope]` (extra work counts as a failure).
5. Report briefly:
   - todo or requirement ✅/❌
   - checks run and their results
   - findings as `[Severity] file:line: issue → fix`
   - verdict: Ready / Ready with notes / Changes required / Unable to verify
6. **Plan mode:** all pass → status `Verified (not human-verified)`, validate. Otherwise leave the plan as is, say "Run `/plan`", and stop.
7. All pass and the target is a branch: run `python3 .claude/scripts/pr_link.py <t>` and show the link. Remind the user to commit and push first and, in plan mode, to test it and then delete ` (not human-verified)` from Status.
