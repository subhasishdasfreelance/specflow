---
name: build
description: Implement the approved todo list of the current branch's plan.
disable-model-invocation: true
---

Ticket: `tickets/<current-branch>.md`. A hook already checked it is `Planned` or `Building` with no ❓ / ⛔ items. Say "on `<current>`". Never create or switch branches, and never overwrite uncommitted changes you didn't make.

**Work:** ticket → `Building`. Then work through the 📝 todos under `Todo:`, using the numbered changes below each:
- Do only what the todos need, following CLAUDE.md › Code. Add tests.
- Todos that touch separate files run in parallel: one subagent each, started in a single message. Only you edit the ticket.
- Change each todo's 📝 to ✅ as soon as it's done, including each parallel one as its subagent reports back.
- Run the project's tests once at the end.

**Stuck** (unclear requirement, technical blocker, scope change): leave the plan as is (only `/plan` writes plan text), explain the problem in chat, stop, and say "Run `/plan`."

**Done:** all ✅ and tests pass → ticket `Built`, validate. Reply in a few lines: files changed, tests. Then "Next: `/verify <base>`", where `<base>` is the branch this one was cut from (the other local branch whose `git merge-base` with HEAD is newest; default branch if unsure). No commits.
