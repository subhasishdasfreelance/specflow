# specflow: plan first, code second

Claude **reads and advises** by default. It writes only when you type a command, and only for that one message. Works for any stack.

## Setup (once per project)
1. Install Claude Code, Python 3 (`python3 --version` must work), git, and Node 18+ or Bun.
2. In your project, run `npx specflow` or `bunx specflow`. It lists every change and asks first. Pin a version with `npx specflow@0.1.0`.
3. Open (or restart) Claude Code and type `/hooks` to check the workflow hooks are listed.

| specflow adds | How |
|---|---|
| `.claude/hooks/`, `.claude/scripts/`, `.claude/skills/`, `.claude/settings.json` | Copied in. Same-name files are overwritten, including your own `.claude/settings.json`. |
| `.github/workflows/specflow-plans.yml` | A GitHub check that fails on every push while any plan is not `Verified`. Your other workflow files are never touched. |
| `README-specflow.md` | This guide. Your `README.md` is never touched. |
| `CLAUDE.md`, `.gitignore` | A block is added at the end between `specflow:start` / `specflow:end` markers. The `CLAUDE.md` block is this repo's `CLAUDE.md`. Your text stays. Re-running replaces the block. |

## Day-to-day
```
talk  →  /plan  →  approve  →  /build  →  /verify  →  you test  →  open the PR
```

| You | Claude |
|---|---|
| `How should we add reminders?` | Reads the code, asks questions, suggests an approach. Writes nothing. |
| `/plan` | Writes `tickets/<branch>.md` for the current branch: a Goal, and 🔲 todos with numbered changes below each. Unclear points become ❓ items. Run it again to revise the plan. |
| *(you)* delete ` (unverified)` from Status | That's your approval. |
| `/build` | Writes the code and tests, turning each 🔲 into ✅. |
| `/verify main` | Reviews the branch against `main` and the plan, runs tests, lint and build, and gives a PR link. |
| *(you)* test it, delete ` (not human-verified)` | That's your sign-off. Commit, push, open the PR. |

**Statuses**
```
Planned (unverified)  →  Planned  →  Building  →  Built  →  Verified (not human-verified)  →  Verified
```
- A note in brackets means "waiting for you". Only you delete it; Claude can't.
- Re-running `/plan` sets `Planned (revised, unverified)`. Delete the note again to approve.
- A command won't start until the previous note is gone. The check is plain Python, so it costs no tokens.
- `Verified (Skipped)`: set it by hand on a plan you won't finish or verify; the plan check skips it.

**Questions and blockers**
- Only `/plan` writes plan text. Each item starts with a mark: 🔲 todo, ✅ done, ❓ question, ⚠️ warning, ⛔ blocked, ❌ out of scope. ❓ and ⛔ sit next to the todo they belong to.
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
- Check plans: `python3 .claude/scripts/validate_plan.py`. Add `--verified` to also fail unless every plan is `Verified`, as the GitHub check does.
- Run the workflow's tests: `python3 -m unittest discover -s tests/workflow -t tests/workflow`. They also need Node, for `npm pack`.

## Changing the workflow itself
Claude can't edit `.claude/`, `CLAUDE.md` or `.git/`. To let it, put `{ "disableAllHooks": true }` in `.claude/settings.local.json`. Delete that file and restart Claude Code when done.

## Uninstall
Close Claude Code, then run `npx specflow --uninstall` (or `bunx specflow --uninstall`) in your project. It lists what it removes and asks first. It removes only what specflow added; a file or folder that still holds your own content is kept.
- If `.claude/settings.json` was yours before, restore it: `git checkout -- .claude/settings.json`.
- `docs/PRD.md` and `tickets/` are plain Markdown. Keep or delete them.
- Reopen Claude Code and check `/hooks` lists no workflow hooks.

## Limits
- The hooks are guardrails, not a sandbox. A program run during `/build` or `/vibe` can still write files.
- `/verify` runs your test, lint and build commands, which may create build output.
- Claude Code must use Bash (Git Bash on Windows) because the hooks block PowerShell. Tests run on Linux, macOS and Windows.

## Releasing
On `main` with nothing uncommitted, run `bun run release:patch "what changed"` (or `release:minor`, `release:major`, `release:alpha`, `release:beta`; with npm: `npm run release:patch -- "what changed"`). It bumps the version, commits, creates the tag with your message and pushes both. The publish workflow puts it on npm.
- Try a prerelease with `npx specflow@alpha` or `npx specflow@beta`.

This repo also holds `bin/specflow.js` (the installer), `package.json`, `.github/workflows/test.yml` and `publish.yml`, and `tests/workflow/`. These aren't installed. Its `CLAUDE.md` is the block added to your `CLAUDE.md`.
