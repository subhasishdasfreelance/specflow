---
name: build
description: Implement the approved todo list of a ticket.
disable-model-invocation: true
argument-hint: "<branch>"
---

Args: `$ARGUMENTS`. Ticket: `tickets/<branch>.md`.

**Check first (stop if any fail):**
- No branch given: ask "Run `/build <branch>`" and stop.
- The ticket validates and is `Planned`, `Building` or `Blocked`. If it's Pending, say "Run `/plan approve <branch>`".
- Say "on `<current>`, ticket `<branch>`". Never create or switch branches. If `<current>` isn't `<branch>`, ask the user whether to build on `<current>`; no: stop.
- Never overwrite uncommitted changes you didn't make.

**Work:** ticket → `Building`. If it was `Blocked`: remove the `- Blocker:` line, untick the todos the blocker is about, and fix them as the current plan says. Then work through `## Todo`:
- Do only what the todos need, following CLAUDE.md › Code. Add tests. Unclear? Ask and stop.
- Todos that touch separate files run in parallel: one subagent each, started in a single message. Only you edit the ticket.
- Tick each todo (`- [x]`) as soon as it's done, including each parallel one as its subagent reports back.
- Run the project's tests once at the end.

Scope change needed: ticket → `Blocked` with a `- Blocker:` line, then say "Run `/plan revise <branch> <change>`".

**Done:** all ticked and tests pass → ticket `Built`, validate. Reply in a few lines: files changed, tests. Then "Next: `/verify <base>`", where `<base>` is the branch `<branch>` was cut from (the other local branch whose `git merge-base` with HEAD is newest; default branch if unsure). No commits.
