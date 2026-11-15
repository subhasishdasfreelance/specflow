---
name: resolve-conflict
description: Pull the target branch into the current branch and resolve merge conflicts. No push.
disable-model-invocation: true
argument-hint: "<target-branch>"
---

Target: `$ARGUMENTS`

1. No target given: show `git branch -a`, ask "Run `/resolve-conflict <branch>`", and stop. If the working tree is dirty: ask the user to commit first, and stop.
2. Say "Merging `<target>` into `<current>`", then run `git pull origin <target> --no-rebase`. If there are no conflicts, report it and stop.
3. For each file in `git diff --name-only --diff-filter=U`: keep both sides' intent, remove the markers, change nothing else, then `git add` it. If a conflict is ambiguous, ask and stop; never guess.
4. Run the project's tests, then `git commit --no-edit`. Reply with the files resolved, the tests, and "Not pushed."
