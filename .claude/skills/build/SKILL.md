---
name: build
description: Implement the approved todo list of the current branch's plan.
disable-model-invocation: true
---

Ticket: `tickets/<current-branch>.md`. A hook already checked it is `Planned` or `Building` with no `## Questions` / `## Blockers`. Say "on `<current>`". Never create or switch branches, and never overwrite uncommitted changes you didn't make.

**Work:** ticket → `Building`. Then work through `## Todo`, using the change written below each todo:
- Do only what the todos need, following CLAUDE.md › Code. Add tests.
- Todos that touch separate files run in parallel: one subagent each, started in a single message. Only you edit the ticket.
- Tick each todo (`- [x]`) as soon as it's done, including each parallel one as its subagent reports back.
- Run the project's tests once at the end.

**Stuck** (unclear requirement, technical blocker, scope change): add a short item under `## Blockers` at the end of the ticket (create the section if needed), keep the status, stop, and say "Answer it, then run `/plan`."

**Done:** all ticked and tests pass → ticket `Built`, validate. Reply in a few lines: files changed, tests. Then "Next: `/verify <base>`", where `<base>` is the branch this one was cut from (the other local branch whose `git merge-base` with HEAD is newest; default branch if unsure). No commits.
