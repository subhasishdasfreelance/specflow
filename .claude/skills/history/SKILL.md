---
name: history
description: Search tickets on all branches for the same or similar work and report how it went.
disable-model-invocation: true
argument-hint: "<topic>"
---

Topic: `$ARGUMENTS`. Read-only: never change files or git state.

1. No topic given: ask "Run `/history <topic>`" and stop.
2. List branches (`git branch -a`). Search tickets everywhere: `git grep -i -l <term> <branch> -- tickets` for each branch, plus the working tree. Try a few synonyms.
3. Read each match: Goal, Status, Blocker, and `git log -1 --format=%cs <branch>`. Also check the code for an existing implementation.
4. Report only, minimal and skimmable:
   - One line per match: `branch` · Status · same / similar · one-line Goal · last change date
   - Blockers, if any
   - Verdict: new / partly done / already done (on which branch)

   Nothing found: say "No earlier tickets for this."
