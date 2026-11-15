---
name: verify
description: Read-only review of the current branch against its ticket and a target branch.
disable-model-invocation: true
argument-hint: "<target-branch>"
---

Args: `$ARGUMENTS`. Ticket: `docs/tickets/<current-branch>.md`. Read-only: never change code or git state. You may edit only the ticket's status lines and `## Verification`.

1. No target given: show `git branch -a` and the current branch, ask "Run `/verify <branch>`", and stop.
2. The ticket must be `Built` and must validate.
3. Changes: `git log <t>..HEAD`, `git diff <t>...HEAD`, `git diff --cached`, `git diff`, and untracked files (`git ls-files --others --exclude-standard`; read them directly).
4. Check each requirement and acceptance criterion. Run the project's existing test, lint and build commands. Review like a PR: bugs, security, missing tests, ticket deviations, bloat.
5. Report briefly:
   - requirement ✅/❌
   - checks run and their results
   - findings as `[Severity] file:line: issue → fix`
   - verdict: Ready / Ready with notes / Changes required / Unable to verify
6. Write a 3-line summary under `## Verification`. All pass: set the ticket to `Verified` and say "Test it, then `/complete <t>`". Otherwise set it to `Blocked` with a `- Blocker:` line.
