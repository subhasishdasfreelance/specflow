feature/updated-instructions
Status: Verified

Goal:
Repos that install specflow get this repo's CLAUDE.md, with every engineering guideline from guidelines.md folded into it, so Claude there stays in analysis mode, still gives the full analysis, points to the next command and follows the same coding rules.

Todo:
✅ CLAUDE.md Code section holds every rule from guidelines.md, merged with the existing bullets and nothing repeated (CLAUDE.md)

  1. CLAUDE.md Code bullet 1: Human-friendly first: readable, explicit and maintainable; clear names, plain flow, explicit over clever.
  2. CLAUDE.md Code bullet 2: Simplest solution that works, and only what was asked. Keep the existing no-bloat list, add "no layers that hide simple logic", keep "Prefer editing to adding files".
  3. CLAUDE.md Code bullet 3 (new): Files under 500 lines, functions and components small; split out a cohesive unit when code gets hard to follow.
  4. CLAUDE.md Code bullet 4: Small, focused diff; match existing patterns. Don't refactor, reformat or touch unrelated code; mention issues instead. Remove only dead code your change created.
  5. CLAUDE.md Code bullet 5: State assumptions and show tradeoffs when there is more than one good option. Define the check first, verify, then stop once the goal is met.
  6. CLAUDE.md Code last bullet (branch names, short replies): no change.


✅ specflow adds this repo's CLAUDE.md, not guidelines.md, as the block in the target CLAUDE.md, and guidelines.md is gone (specflow, guidelines.md)

  1. specflow header comment: say it adds CLAUDE.md to the end of the target CLAUDE.md.
  2. specflow tar extract list: replace '*/guidelines.md' with '*/CLAUDE.md'.
  3. specflow printf preview line: label it "CLAUDE.md (workflow block)".
  4. specflow add_block call for CLAUDE.md: use the text of "$src/CLAUDE.md".
  5. guidelines.md: delete the file.


✅ The installer tests expect the CLAUDE.md block and pass (tests/workflow/test_specflow.py)

  1. setUp: drop guidelines.md from the git ls-files list and remove the "not committed yet" fallback.
  2. setUp: rename self.guidelines to self.block and read it from REPO / "CLAUDE.md".
  3. test_fresh_project: compare the target CLAUDE.md with the markers around self.block.
  4. test_fresh_project: keep the check that guidelines.md is not created in the target.


✅ The README says the block comes from this repo's CLAUDE.md (README.md)

  1. README.md "specflow adds" table, CLAUDE.md row: say the block is this repo's CLAUDE.md.
  2. README.md last line: drop guidelines.md and say CLAUDE.md is the block added to the target CLAUDE.md.


✅ In other repos every analysis reply starts with "Analysis only mode." and still gives the full analysis, ending with "Run /plan.", including when the user asks for a change in plain words (CLAUDE.md)

  1. CLAUDE.md Workflow, "Default = analysis" line: replace 'If asked to change something, say only "Analysis only mode."' with 'Start every analysis reply with "Analysis only mode.", then give the full analysis, even if asked to change something'.
  2. Keep "(never explain hooks or blocks)" right after it.
  3. Keep the rest of that line (the Report list and "Run /plan.") as it is.


⚠️ /build can edit CLAUDE.md only while hooks stay off here (.claude/settings.local.json has disableAllHooks)

  1. The hooks treat CLAUDE.md as protected in every mode.


⚠️ Changes reach other repos only after this is merged to main and specflow is run again there

  1. specflow downloads from GitHub main by default.
