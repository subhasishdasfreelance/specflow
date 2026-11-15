# Spec-driven workflow for Claude Code

A small setup that makes Claude **think first, plan second, and code only when you say so**.
It works for any kind of project: backend, frontend, Android, iOS, scripts. Nothing here is tied to a language or framework.

## In one minute
- Talk to Claude normally and it only **reads and advises**. It won't change files.
- You type a **command** (like `/build`) to let it write. That permission lasts for **one message only**.
- Everything is written down in two places:
  - `docs/PRD.md`: what the product is (the big picture).
  - `tickets/<branch>.md`: what this branch builds (one ticket per branch).
- When something is unclear, Claude **asks you** instead of guessing.

## Setup (once per project)
1. Install Claude Code, Python 3, git, curl and tar. Install `gh` if you want `/complete` to open PRs.
2. Copy the `specit` script from this repo to a folder on your `PATH` (e.g. `~/.local/bin/`) and make it executable: `chmod +x ~/.local/bin/specit`.
3. Set `GITHUB_TOKEN` to a token that can read this repo.
4. In your project folder, run `specit` (or `specit <branch|tag|commit>`). It lists every change and asks before doing anything.
5. Open the project in Claude Code (restart it if it was already open), type `/hooks` and check the workflow hooks are listed.

**What `specit` adds to your project**

| Item | What happens |
|---|---|
| `.claude/hooks/`, `.claude/scripts/validate_plan.py`, `.claude/skills/`, `.claude/settings.json` | Copied in. Files with the same name are overwritten (the list shows `overwrite`), including your own `.claude/settings.json` if you had one. |
| `README-specit.md` | This guide. Your own `README.md` is never touched. |
| `CLAUDE.md` | The engineering guidelines are added **at the end**, between `<!-- specit:start -->` and `<!-- specit:end -->`. Your text stays as it is. Created if missing. |
| `.gitignore` | `.claude/runtime/` and `.claude/settings.local.json` are added at the end, between `# specit:start` and `# specit:end`. Created if missing. |

Running `specit` again replaces the marked blocks instead of adding new ones. While you use the workflow, the hooks also create `.claude/runtime/` (session state) and `__pycache__/` folders under `.claude/`.

## Day-to-day
```
/prd  →  talk  →  /plan  →  /plan approve  →  /build  →  /verify  →  you test  →  /complete
```

| # | You type | What Claude does |
|---|---|---|
| 1 | `/prd A booking app for small clinics, web + Android` | Asks questions about anything vague, then writes `docs/PRD.md`. Skip this if you already have a PRD. |
| 2 | `How should we add appointment reminders?` | Reads the code and other branches' tickets, asks questions, suggests an approach. Writes nothing. |
| 3 | `/plan feature/reminders` | Writes `tickets/feature/reminders.md` (goal and todo list). |
| 4 | `/plan revise feature/reminders Also send SMS` | Updates the ticket. |
| 5 | `/plan approve feature/reminders` | Marks the ticket approved. Nothing else changes. |
| 6 | `/build feature/reminders` | Stays on the current branch (asks if it isn't `feature/reminders`) and writes the code and tests, ticking off the todo list. |
| 7 | `/verify main` | Reviews the branch against `main` (`/build` suggests the branch you cut from), runs your tests, lint and build. Changes no code. |
| 8 | (you) | Try it yourself. |
| 9 | `/complete main` | Marks it human verified, commits, pushes and opens a PR into `main`. |

**Other commands**
- `/vibe Fix the typo on the login page`: a quick change without a ticket. Good for tiny fixes and experiments.
- `/resolve-conflict main`: pulls `main` into your branch, fixes the conflicts, runs tests and commits. **It does not push**; you push.

## Good to know
- **Name your branch.** Any name works: `feature/x`, `bugfix/y`, `JIRA-123`. A `/` in the name becomes a folder under `tickets/`.
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

## Uninstall
Claude can't remove the workflow (the hooks block it), so do it yourself. The steps below remove only what `specit` added and leave everything else in place.

**What gets removed**
- Files: `README-specit.md`, `.claude/settings.json`, `.claude/scripts/validate_plan.py`, the 7 `.claude/hooks/workflow_*.py` files, and the `.claude/skills/` files of `build`, `complete`, `plan`, `prd`, `resolve-conflict`, `verify` and `vibe`.
- Folders the workflow created: `.claude/runtime/` and `.claude/*/__pycache__/`.
- Folders left empty afterwards (a folder that still has your files in it is kept).
- The marked block at the end of `CLAUDE.md` and of `.gitignore`. Either file is deleted only if nothing else is left in it.

**Steps**
1. Close Claude Code.
2. In your project folder, run:
   ```bash
   rm -f README-specit.md .claude/settings.json .claude/scripts/validate_plan.py \
     .claude/hooks/workflow_{bash,policy,pre_tool,prompt_expansion,prompt_submit,state,stop}.py \
     .claude/skills/{build,complete,plan,prd,resolve-conflict,verify,vibe}/SKILL.md \
     .claude/skills/plan/plan-template.md .claude/skills/prd/prd-template.md
   rm -r .claude/runtime .claude/*/__pycache__ 2>/dev/null
   rmdir .claude/skills/{build,complete,plan,prd,resolve-conflict,verify,vibe} \
     .claude/skills .claude/hooks .claude/scripts .claude 2>/dev/null
   for f in CLAUDE.md .gitignore; do
     [ -f "$f" ] || continue
     awk '/^(<!-- |# )specit:start/ {skip = 1} !skip {print} /^(<!-- |# )specit:end/ {skip = 0}' "$f" > "$f.tmp"
     cat "$f.tmp" > "$f" && rm "$f.tmp"
     [ -s "$f" ] || rm "$f"
   done
   ```
   If `.claude/settings.json` was yours before you installed specit, restore it from git (`git checkout -- .claude/settings.json`) instead of deleting it.
3. Keep or delete `docs/PRD.md` and `tickets/`. They're plain Markdown and still useful as a record.
4. Reopen Claude Code and type `/hooks` to check that no workflow hooks are listed.

## Limits
- The hooks are guardrails, not a sandbox. A program run during `/build` or `/vibe` (e.g. a test script) can still write files.
- `/verify` runs your test, lint and build commands, which may create build output. Source edits stay blocked.
- Bash only (PowerShell is blocked). Tested on Linux.
- Pressing Esc mid-reply is fine: the next message resets to read-only anyway.

## Files
```
CLAUDE.md                      your rules, plus the guidelines block specit adds
README-specit.md               this guide
docs/PRD.md                    the product
tickets/<branch>.md            one ticket per branch
.claude/skills/                the commands
.claude/hooks/                 enforcement
.claude/scripts/validate_plan.py
```
This repo also holds `specit` (the installer), `guidelines.md` (the block added to `CLAUDE.md`) and `tests/workflow/` (tests for the hooks and the installer). These are not installed into your project.
