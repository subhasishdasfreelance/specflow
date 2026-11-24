# Workflow (hooks enforce this)

Works for any stack (backend, frontend, mobile, etc.): use the project's own tools and conventions.

**Default = analysis.** Read, search, ask. Never write or run mutating commands, even if asked in plain words; point to `/vibe`, `/plan` or `/prd`. If asked to change something, say only "Analysis only mode." (never explain hooks or blocks). Check existing code before proposing; check other tickets only via `/history`. Report: problem, FR/NFR/BR, acceptance criteria, approach, files, risks, questions. Then: "Run `/plan`."

**Never assume.** If anything that affects the result is ambiguous, ask numbered questions and stop. Don't guess.

**Commands** (user-only, one turn; a follow-up is analysis again): `/prd` · `/plan` · `/build` · `/verify <target>` · `/vibe` · `/resolve-conflict <target>` · `/history <topic>` (read-only).

**Truth:** `docs/PRD.md` covers the product (no stories, no history). `tickets/<branch>.md` holds one plan per branch and is the source of truth for that work. Scope changes go only through re-running `/plan`.

**Statuses:** `Planned (unverified) → Planned → Building → Built → Verified (not human-verified) → Verified`. A re-run of `/plan` sets `Planned (revised, unverified)`. Only the user deletes a note in brackets. Only `/plan` writes plan text: requirement or technical problems go in as ❓ / ⛔ items next to their todo, and only those stop `/build`. Validate with `python3 .claude/scripts/validate_plan.py`

## Code
- Human-friendly first: readable, explicit and maintainable; clear names, plain flow, explicit over clever.
- Simplest solution that works, and only what was asked. No bloat: no speculative features, abstractions, config, wrappers, boilerplate, impossible-case handling, or comments that restate the code; no layers that hide simple logic. Prefer editing to adding files.
- Files under 500 lines, functions and components small; split out a cohesive unit when code gets hard to follow.
- Small, focused diff; match existing patterns. Don't refactor, reformat or touch unrelated code; mention issues instead. Remove only dead code your change created.
- State assumptions and show tradeoffs when there is more than one good option. Define the check first, verify, then stop once the goal is met.
- Always name the current and target branch. Keep replies minimal and skimmable: short bullets, no preamble, no filler.
