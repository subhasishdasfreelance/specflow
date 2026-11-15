---
name: build
description: Implement the approved tasks of a ticket.
disable-model-invocation: true
argument-hint: "<branch> [TASK-###]"
---

Args: `$ARGUMENTS`. Ticket: `docs/tickets/<branch>.md`.

**Check first (stop if any fail):**
- No branch given: ask "Run `/build <branch>`" and stop.
- The ticket validates and is `Planned` or `Building`. If it's Pending, say "Run `/plan approve <branch>`".
- Say "on `<current>` → `<branch>` (base `<Base>`)". On Base with `<branch>` not yet created: `git switch -c <branch>`. On any other branch: stop.
- Never overwrite uncommitted changes you didn't make.

**Work:** ticket → `Building`. Then for each approved task, in dependency order:
1. Task → `Building`.
2. Implement only its `Done when`, following CLAUDE.md › Code. Unclear? Ask and stop.
3. Add tests and run them with the project's own tooling.
4. Task → `Built` once its checks pass.

Scope change needed: set the task to `Blocked` with a `- Blocker:` line, then say "Run `/plan revise <branch> <change>`".

**Done:** ticket → `Built`, validate. Reply in a few lines: tasks done, files changed, tests. Then "Next: `/verify <Base>`." No commits.
