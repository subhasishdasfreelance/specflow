---
name: plan
description: Create, revise or approve a ticket (docs/tickets/<branch>.md).
disable-model-invocation: true
argument-hint: "<branch> | revise <branch> <change> | approve <branch>"
---

Args: `$ARGUMENTS`. Write only `docs/tickets/<branch>.md` (a branch `feature/login` → `docs/tickets/feature/login.md`). Never code, never the PRD.

**Create** (`<branch>`):
1. No branch given: ask "Run `/plan <branch>`" and stop.
2. Use the analysis from this conversation. Read `docs/PRD.md`, existing tickets and `git status`. If another branch already covers this (`git grep -i <term> <branch> -- docs/tickets`), stop and report it. If it conflicts with the PRD, say "Run `/prd <change>` first" and stop.
3. Anything unclear (behaviour, edge cases, Base branch)? Ask numbered questions and stop. Never guess.
4. Write the ticket from [plan-template.md](plan-template.md): testable FR/NFR/BR, few meaningful tasks, everything `Pending`.
5. Validate, reply in a few lines, end with "Run `/plan approve <branch>`."

**revise `<branch> <change>`:** ask if the change is unclear. Update the ticket, keeping unaffected IDs and statuses; changed tasks and the ticket go back to `Pending`. Add a History line, validate, summarize in 2-3 lines.

**approve `<branch>`:** statuses only: the ticket and its Pending tasks become `Planned`. Add a History line, validate. Reply "Approved. Run `/build <branch>`."
