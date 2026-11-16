---
name: verify
description: Claude reviews the current branch against its ticket and a target branch, or records that a human tested it.
disable-model-invocation: true
argument-hint: "<target-branch> | human <target-branch>"
---

Args: `$ARGUMENTS`. Ticket: `tickets/<current-branch>.md`. Read-only: never change code or git state (no commits, no pushes). You may edit only the ticket's `Status`/`Blocker` lines.

1. No target given: show `git branch -a` and the current branch, ask "Run `/verify <target>` or `/verify human <target>`", and stop.
2. The ticket must validate and be `Built` or one of the verified statuses.
3. **`/verify human <t>`** (the user tested it by hand): add `Human verified` to the status and skip to step 6.
4. **`/verify <t>`** (Claude reviews): read `git log <t>..HEAD`, `git diff <t>...HEAD`, `git diff --cached`, `git diff`, and untracked files (`git ls-files --others --exclude-standard`; read them directly). Check each todo's outcome. Run the project's existing test, lint and build commands. Review like a PR: bugs, security, missing tests, ticket deviations, bloat. Flag every change not needed by the Goal or a todo as `[Scope]` (extra work counts as a failure).
5. Report briefly:
   - todo ✅/❌
   - checks run and their results
   - findings as `[Severity] file:line: issue → fix`
   - verdict: Ready / Ready with notes / Changes required / Unable to verify

   All pass: add `Claude verified` to the status. Otherwise set it to `Blocked` with a `- Blocker:` line and stop.
6. Adding to the status: `Built` → the new one; the other one → `<other> + <new>`; already there → no change. Validate.
7. Both verifications present: give a PR link, `https://github.com/<owner>/<repo>/compare/<t>...<branch>?expand=1&body=<body>` (owner/repo from `git remote get-url origin`, body URL-encoded). No title (the user fills it in). Body: the ticket's Goal only, without the branch name or ticket path. Remind the user to commit and push first. Otherwise say which verification is still missing.
