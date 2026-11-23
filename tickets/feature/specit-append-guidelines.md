# feature/specit-append-guidelines

- Status: Verified

## Goal
People using specit follow a simpler workflow: they approve by deleting a note in brackets, read plans easily, and spend fewer tokens because checks run without AI.

## Todo

---

- [x] **Plans accept only the new statuses, need changes under each todo, and may end with `## Questions` / `## Blockers`** (.claude/scripts/validate_plan.py, tests/workflow/test_validate_plan.py, tests/workflow/helpers.py)
  - `STATUSES`: `Planned (unverified)`, `Planned (revised, unverified)`, `Planned`, `Building`, `Built`, `Verified (not human-verified)`, `Verified`.
  - Drop `Blocker` and the required `## Changes`.
  - Error "todo has no change" when no indented line follows a todo.

---

- [x] **Claude can't remove a note in brackets or skip a stage** (.claude/hooks/workflow_policy.py, tests/workflow/test_hooks.py)
  - `/plan`: new ticket → `Planned (unverified)`; existing → `Planned (revised, unverified)`.
  - `/build`: `Planned` → `Building` → `Built`. `/verify`: `Built` → `Verified (not human-verified)`.
  - `/build` and `/verify` may only add to `## Blockers`. The `approve` logic is gone.

---

- [x] **A wrong branch or status refuses `/plan`, `/build` or `/verify` with a one-line reason before Claude runs** (.claude/hooks/workflow_precheck.py, .claude/hooks/workflow_prompt_expansion.py, tests/workflow/test_precheck.py)
  - `precheck(command, args)` returns a reason or `None`.
  - Reads the branch (`git branch --show-current`), `branch-pattern:` from `plan/SKILL.md`, and the ticket.
  - `/build` is also refused while `## Questions` / `## Blockers` exist.
  - The expansion hook prints `{"decision": "block", "reason": ...}`.

---

- [x] **`python3 .claude/scripts/pr_link.py <target>` prints the PR link, and `/verify` can run it** (.claude/scripts/pr_link.py, .claude/hooks/workflow_bash.py, .claude/settings.json, tests/workflow/test_pr_link.py)
  - Owner and repo come from `git remote get-url origin` (ssh, ssh host alias or https).
  - Body is the ticket's Goal, encoded with `urllib.parse.quote`.

---

- [x] **`/plan` uses the current branch, creates or revises the one plan, and writes unknowns under `## Questions`** (.claude/skills/plan/SKILL.md)
  - Frontmatter `branch-pattern: ^(feature|bug)/[A-Za-z0-9-]+$`.
  - No `approve` or `revise`. On revise, keep unaffected ticks and remove answered questions and blockers.

---

- [x] **Plans are easy to read: each todo is its own block with its changes as bullets** (.claude/skills/plan/plan-template.md, .claude/skills/plan/SKILL.md, tests/workflow/test_validate_plan.py)
  - `---` before and after each todo; bold outcome; indented change bullets.

---

- [x] **`/build` adds problems under `## Blockers`; `/verify` has no `human` mode, gives the PR link, and can review a PR or branch against a pasted requirement** (.claude/skills/build/SKILL.md, .claude/skills/verify/SKILL.md)
  - Remove `Blocked` and the checks the precheck now does.
  - PR review mode never touches a ticket.

---

- [x] **The installer and the uninstall script include the new files** (README.md, tests/workflow/test_specit.py)
  - `pr_link.py` and `workflow_precheck.py` are in the uninstall `rm -f` list.

---

- [x] **The README is short and plain and describes the new workflow** (README.md)
  - Covers the lifecycle, notes in brackets, `## Questions` / `## Blockers`, PR review and `branch-pattern`.

---
