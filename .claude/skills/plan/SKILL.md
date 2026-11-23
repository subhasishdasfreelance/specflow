---
name: plan
description: Create or revise the plan for the current branch (tickets/<branch>.md).
disable-model-invocation: true
argument-hint: "[change or answers]"
branch-pattern: ^(feature|bug)/[A-Za-z0-9-]+$
---

Args: `$ARGUMENTS`. Branch: the current git branch (a hook already checked it against `branch-pattern` above; edit that line to change the format). Write only `tickets/<branch>.md` (`feature/login` → `tickets/feature/login.md`). Never code, never the PRD.

1. Use the analysis from this conversation and the args. Read `docs/PRD.md` (if any) and the ticket (if any). If another branch already covers this (`git grep -i <term> <branch> -- tickets`), stop and report it. If it conflicts with the PRD, say "Run `/prd <change>` first" and stop.
2. **No ticket:** write it from [plan-template.md](plan-template.md), status `Planned (unverified)`.
   **Ticket exists:** revise it. If it is in the old structure (no line starting with `Status:`), rewrite it in the template's structure. Keep unaffected ✅ marks and ⚠️ / ❌ items, work the answers into the Goal and todos, and turn answered ❓ and ⛔ items into 📝 todos (or drop them). Status `Planned (revised, unverified)`.
3. Anything unclear about the requirement or the technical approach? Add it as a ❓ item under `Todo:`, next to the todo it belongs to. Never guess. Only `/plan` writes plan text: ❓ question, ⚠️ warning, ⛔ blocked, ❌ out of scope.
4. Keep it brief and skimmable:
   - Plain, everyday words. Short sentences, no jargon, no filler.
   - The heading is just the branch name; the Goal is one sentence.
   - Todos: no overlap, together they deliver the whole Goal, nothing beyond it. Each is a testable outcome and names its files.
   - Follow the template: one line per item, starting with its mark, in plain words (no backticks or other markup). One blank line, then its changes as short indented lines numbered `1.`, `2.`, `3.`. Two blank lines before the next item.
   - Each change is short but technical: the file, the function or field, and what changes, in words a junior developer understands. The developer must always know which code will change.
   - Easy reading beats everything else.
5. Validate. Reply in 2-3 lines, then: "Review it, delete the note in brackets from Status to approve, then run `/build`."
