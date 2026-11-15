# Spec-driven workflow for Claude Code

A small setup that makes Claude **think first, plan second, and code only when you say so**.
It works for any kind of project: backend, frontend, Android, iOS, scripts. Nothing here is tied to a language or framework.

## In one minute
- Talk to Claude normally and it only **reads and advises**. It won't change files.
- You type a **command** (like `/build`) to let it write. That permission lasts for **one message only**.
- Everything is written down in two places:
  - `docs/PRD.md`: what the product is (the big picture).
  - `docs/tickets/<branch>.md`: what this branch builds (one ticket per branch).
- When something is unclear, Claude **asks you** instead of guessing.

## Setup (once per project)
1. Install Claude Code, Python 3 and git. Install `gh` if you want `/complete` to open PRs.
2. Copy `.claude/`, `CLAUDE.md` and `.gitignore` into your project.
3. Open the project in Claude Code (restart it if it was already open).
4. Type `/hooks` and check the workflow hooks are listed.

## Day-to-day
```
/prd  →  talk  →  /plan  →  /plan approve  →  /build  →  /verify  →  you test  →  /complete
```

| # | You type | What Claude does |
|---|---|---|
| 1 | `/prd A booking app for small clinics, web + Android` | Asks questions about anything vague, then writes `docs/PRD.md`. Skip this if you already have a PRD. |
| 2 | `How should we add appointment reminders?` | Reads the code and other branches' tickets, asks questions, suggests an approach. Writes nothing. |
| 3 | `/plan feature/reminders` | Writes `docs/tickets/feature/reminders.md` (requirements, tasks, checks). |
| 4 | `/plan revise feature/reminders Also send SMS` | Updates the ticket. |
| 5 | `/plan approve feature/reminders` | Marks the ticket approved. Nothing else changes. |
| 6 | `/build feature/reminders` | Creates or switches to that branch and writes the code and tests, task by task. |
| 7 | `/verify main` | Reviews the branch against `main`, runs your tests, lint and build. Changes no code. |
| 8 | (you) | Try it yourself. |
| 9 | `/complete main` | Marks it human verified, commits, pushes and opens a PR into `main`. |

**Other commands**
- `/vibe Fix the typo on the login page`: a quick change without a ticket. Good for tiny fixes and experiments.
- `/resolve-conflict main`: pulls `main` into your branch, fixes the conflicts, runs tests and commits. **It does not push**; you push.

## Good to know
- **Name your branch.** Any name works: `feature/x`, `bugfix/y`, `JIRA-123`. A `/` in the name becomes a folder under `docs/tickets/`.
- **One command = one message.** After `/build`, if you say "also fix X", Claude is back to read-only. Run a command again.
- **Plain words never write.** "Please implement it" gets advice, not code.
- **Ticket statuses** move in this order, and each command may only set its own:

| Status | Set by |
|---|---|
| Pending | `/plan` |
| Planned | `/plan approve` |
| Building, Built | `/build` |
| Verified | `/verify` |
| Human verified | `/complete` |
| Blocked | `/plan`, `/build`, `/verify` (with a reason) |

- Check tickets are well-formed: `python3 .claude/scripts/validate_plan.py`
- Run the workflow's own tests: `python3 -m unittest discover -s tests/workflow -t tests/workflow`

## Changing the workflow itself
Claude can never edit `.claude/`, `CLAUDE.md` or `.git/`. To change them with Claude's help, put this in `.claude/settings.local.json`:
```json
{ "disableAllHooks": true }
```
Delete that file and restart Claude Code when you're done.

## Limits
- The hooks are guardrails, not a sandbox. A program run during `/build` or `/vibe` (e.g. a test script) can still write files.
- `/verify` runs your test, lint and build commands, which may create build output. Source edits stay blocked.
- Bash only (PowerShell is blocked). Tested on Linux.
- Pressing Esc mid-reply is fine: the next message resets to read-only anyway.

## Files
```
CLAUDE.md                      rules Claude reads every session
docs/PRD.md                    the product
docs/tickets/<branch>.md       one ticket per branch
.claude/skills/                the commands
.claude/hooks/                 enforcement
.claude/scripts/validate_plan.py
tests/workflow/                tests for the hooks
```
