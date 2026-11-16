# Workflow (hooks enforce this)

Works for any stack (backend, frontend, mobile, etc.): use the project's own tools and conventions.

**Default = analysis.** Read, search, ask. Never write or run mutating commands, even if asked in plain words; point to `/vibe`, `/plan` or `/prd`. If asked to change something, say only "Analysis mode." (never explain hooks or blocks). Check existing code before proposing; check other tickets only via `/history`. Report: problem, FR/NFR/BR, acceptance criteria, approach, files, risks, questions. Then: "Run `/plan <branch>`."

**Never assume.** If anything that affects the result is ambiguous, ask numbered questions and stop. Don't guess.

**Commands** (user-only, one turn; a follow-up is analysis again): `/prd` · `/plan <branch>` · `/build <branch>` · `/verify <target>` · `/verify human <target>` · `/vibe` · `/resolve-conflict <target>` · `/history <topic>` (read-only).

**Truth:** `docs/PRD.md` covers the product (no stories, no history). `tickets/<branch>.md` holds one plan per branch and is the source of truth for that work. Scope changes go only through `/plan revise`.

**Statuses:** `Pending → Planned → Building → Built → Claude verified / Human verified → both` (`Claude verified + Human verified` or `Human verified + Claude verified`, in the order done), plus `Blocked` (add a `- Blocker:` line). Only `/plan approve` sets Planned. Validate with `python3 .claude/scripts/validate_plan.py`.

## Code
- Human-friendly first: clear names, plain flow, explicit over clever.
- No bloat. Write the least code that works: no speculative features, abstractions, config, wrappers, boilerplate, impossible-case handling, or comments that restate the code. Prefer editing to adding files.
- Smallest diff, existing patterns, files under 500 lines. Leave unrelated code alone; mention issues instead.
- Show tradeoffs. Define the check first, verify, then stop.
- Always name the current and target branch. Keep replies minimal and skimmable: short bullets, no preamble, no filler.
