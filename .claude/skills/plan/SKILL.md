---
name: plan
description: Create, revise or approve a ticket (tickets/<branch>.md).
disable-model-invocation: true
argument-hint: "<branch> | revise <branch> <change> | approve <branch>"
---

Args: `$ARGUMENTS`. Write only `tickets/<branch>.md` (a branch `feature/login` → `tickets/feature/login.md`). Never code, never the PRD.

**Create** (`<branch>`):
1. No branch given: ask "Run `/plan <branch>`" and stop.
2. Use the analysis from this conversation. Read `docs/PRD.md`, existing tickets and `git status`. If another branch already covers this (`git grep -i <term> <branch> -- tickets`), stop and report it. If it conflicts with the PRD, say "Run `/prd <change>` first" and stop.
3. Anything unclear (behaviour, edge cases)? Ask numbered questions and stop. Never guess.
4. Write the ticket from [plan-template.md](plan-template.md), status `Pending`. Keep it brief, aim for under 20 lines:
   - Plain, everyday words a newcomer understands. Short sentences, no jargon, no filler.
   - The heading is just the branch name; the Goal says what it's for.
   - Skimmable: one short line per bullet, one idea per line.
   - Todo: mutually exclusive (no two items overlap), exhaustive (together they deliver the whole Goal), minimal (fewest items, nothing beyond the Goal). Each is a testable outcome (it doubles as the acceptance check) and names the files it touches.
   - Changes (last section, numbered `1.`, `2.`): the overall technical changes. Mutually exclusive, minimal and exhaustive, like the todos. Detailed enough for a developer to act on, but brief.
5. Validate, reply in a few lines, end with "Run `/plan approve <branch>`."

**revise `<branch> <change>`:** ask if the change is unclear. Update the ticket, keeping unaffected ticks; status goes back to `Pending`. Validate, summarize in 2-3 lines.

**approve `<branch>`:** status only: `Pending` → `Planned`. Validate. Reply "Approved. Run `/build <branch>`."
