# specit: plan first, code second

Claude **reads and advises** by default. It writes only when you type a command, and only for that one message. Works for any stack.

## Setup (once per project)
1. Install Claude Code, Python 3, git, curl and tar.
2. Put the `specit` script from this repo on your `PATH` (e.g. `~/.local/bin/`) and `chmod +x` it.
3. Set `GITHUB_TOKEN` to a token that can read this repo.
4. In your project, run `specit` (or `specit <branch|tag|commit>`). It lists every change and asks first.
5. Open (or restart) Claude Code and type `/hooks` to check the workflow hooks are listed.

| specit adds | How |
|---|---|
| `.claude/hooks/`, `.claude/scripts/`, `.claude/skills/`, `.claude/settings.json` | Copied in. Same-name files are overwritten, including your own `.claude/settings.json`. |
| `README-specit.md` | This guide. Your `README.md` is never touched. |
| `CLAUDE.md`, `.gitignore` | A block is added at the end between `specit:start` / `specit:end` markers. Your text stays. Re-running replaces the block. |

## Day-to-day
```
talk  →  /plan  →  approve  →  /build  →  /verify  →  you test  →  open the PR
```

| You | Claude |
|---|---|
| `How should we add reminders?` | Reads the code, asks questions, suggests an approach. Writes nothing. |
| `/plan` | Writes `tickets/<branch>.md` for the current branch: a Goal, and 📝 todos with numbered changes below each. Unclear points become ❓ items. Run it again to revise the plan. |
| *(you)* delete ` (unverified)` from Status | That's your approval. |
| `/build` | Writes the code and tests, turning each 📝 into ✅. |
| `/verify main` | Reviews the branch against `main` and the plan, runs tests, lint and build, and gives a PR link. |
| *(you)* test it, delete ` (not human-verified)` | That's your sign-off. Commit, push, open the PR. |

**Statuses**
```
Planned (unverified)  →  Planned  →  Building  →  Built  →  Verified (not human-verified)  →  Verified
```
- A note in brackets means "waiting for you". Only you delete it; Claude can't.
- Re-running `/plan` sets `Planned (revised, unverified)`. Delete the note again to approve.
- A command won't start until the previous note is gone. The check is plain Python, so it costs no tokens.

**Questions and blockers**
- Only `/plan` writes plan text. Each item starts with a mark: 📝 todo, ✅ done, ❓ question, ⚠️ warning, ⛔ blocked, ❌ out of scope. ❓ and ⛔ sit next to the todo they belong to.
- `/build` and `/verify` change only statuses. When stuck or a check fails, they explain in chat and you run `/plan`.
- While any ❓ or ⛔ is left, `/build` won't run. Talk it through, then run `/plan` to fold the answers in.
- Tickets in the old structure (no `Status:` line at the start of a line) are skipped.

**Other commands**
- `/verify <PR link or branch> <requirement>`: reviews any PR or branch against a requirement you paste. Touches no plan.
- `/vibe Fix the login typo`: a quick change without a plan.
- `/prd <product idea>`: writes `docs/PRD.md`, the big picture.
- `/history reminders`: finds earlier plans for similar work. Read-only.
- `/resolve-conflict main`: merges `main` in, fixes conflicts, runs tests, commits. You push.

## Good to know
- **Branch names** must look like `feature/<ticket-id>` or `bug/<ticket-id>`; `/plan` refuses `main` and anything else. To change the format, edit `branch-pattern:` at the top of `.claude/skills/plan/SKILL.md`.
- **One branch, one plan.** `feature/x` → `tickets/feature/x.md`.
- **Plain words never write.** "Please implement it" gets advice, not code.
- Check plans: `python3 .claude/scripts/validate_plan.py`
- Run the workflow's tests: `python3 -m unittest discover -s tests/workflow -t tests/workflow`

## Changing the workflow itself
Claude can't edit `.claude/`, `CLAUDE.md` or `.git/`. To let it, put `{ "disableAllHooks": true }` in `.claude/settings.local.json`. Delete that file and restart Claude Code when done.

## Uninstall
Close Claude Code, then run this in your project. It removes only what specit added. A file or folder that still holds your own content is kept.
```bash
rm -f README-specit.md .claude/settings.json \
  .claude/scripts/{validate_plan,pr_link}.py \
  .claude/hooks/workflow_{bash,policy,precheck,pre_tool,prompt_expansion,prompt_submit,state,stop}.py \
  .claude/skills/{build,history,plan,prd,resolve-conflict,verify,vibe}/SKILL.md \
  .claude/skills/plan/plan-template.md .claude/skills/prd/prd-template.md
rm -r .claude/runtime .claude/*/__pycache__ 2>/dev/null
rmdir .claude/skills/{build,history,plan,prd,resolve-conflict,verify,vibe} \
  .claude/skills .claude/hooks .claude/scripts .claude 2>/dev/null
for f in CLAUDE.md .gitignore; do
  [ -f "$f" ] || continue
  awk '/^(<!-- |# )specit:start/ {skip = 1} !skip {print} /^(<!-- |# )specit:end/ {skip = 0}' "$f" > "$f.tmp"
  cat "$f.tmp" > "$f" && rm "$f.tmp"
  [ -s "$f" ] || rm "$f"
done
```
- If `.claude/settings.json` was yours before, restore it: `git checkout -- .claude/settings.json`.
- `docs/PRD.md` and `tickets/` are plain Markdown. Keep or delete them.
- Reopen Claude Code and check `/hooks` lists no workflow hooks.

## Limits
- The hooks are guardrails, not a sandbox. A program run during `/build` or `/vibe` can still write files.
- `/verify` runs your test, lint and build commands, which may create build output.
- Bash only (no PowerShell). Tested on Linux.

This repo also holds `specit` (the installer), `guidelines.md` (the block added to `CLAUDE.md`) and `tests/workflow/`. These aren't installed.
