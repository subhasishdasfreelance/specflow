feature/simpler-plan
Status: Verified

Goal:
People can read and edit plans in any plain text editor: each plan keeps its .md file but uses a simple structure with emoji marks and short technical changes, only /plan writes plan text, and questions and blockers sit next to the todos they belong to.

Todo:
✅ New plans use the new structure in tickets/<branch>.md (.claude/skills/plan/plan-template.md)

  1. plan-template.md line 1: the branch name; line 2: "Status: <value>" with no leading dash.
  2. plan-template.md: plain "Goal:" and "Todo:" headings replace "## Goal" / "## Todo"; no ---, **, checkboxes or backticks.
  3. plan-template.md: each item is one line starting with a mark: 🔲 todo, ✅ done, ❓ question, ⚠️ warning, ⛔ blocked, ❌ out of scope.
  4. plan-template.md: each item has indented changes numbered 1., 2., 3.
  5. The "## Questions" and "## Blockers" sections are gone; ❓ and ⛔ items replace them.


✅ The validator checks the new structure and reports open ❓ and ⛔ items (.claude/scripts/validate_plan.py)

  1. parse() returns status, sections and items; each item is [mark, text, has_change].
  2. validate() errors on: missing Status, Goal or Todo; invalid status; no 🔲 or ✅ item; duplicate items; an item with no numbered change; backticks in item text.
  3. validate() errors when the status is Built or Verified but a 🔲 remains.
  4. New open_items(text) returns the ❓ and ⛔ items; the hooks use it.
  5. New is_new_structure(text) is true when a line starts with "Status:".
  6. ticket_files() returns only tickets where is_new_structure() is true, so old tickets are skipped.


✅ Hooks refuse /build while any ❓ or ⛔ remains, and let /build and /verify change only statuses (.claude/hooks/workflow_precheck.py, .claude/hooks/workflow_policy.py, .claude/scripts/pr_link.py)

  1. workflow_precheck.py ticket_text() returns None for an old-structure ticket, so /build says "no plan".
  2. workflow_precheck.py precheck() refuses /build when open_items() is not empty.
  3. workflow_policy.py: FREE_LINE matches "Status:"; normalize() turns a leading ✅ back into 🔲 before comparing, so 🔲 to ✅ is the only allowed mark change.
  4. workflow_policy.py: split_blockers() is removed; plan_decision() denies /build and /verify any text change.
  5. pr_link.py goal() reads the lines under "Goal:" and returns "" for an old-structure ticket.


✅ The skills and docs describe the new structure and who writes what (.claude/skills/plan/SKILL.md, .claude/skills/build/SKILL.md, .claude/skills/verify/SKILL.md, .claude/skills/history/SKILL.md, CLAUDE.md, README.md)

  1. plan/SKILL.md: writes the new structure, rewrites an old-structure ticket, turns answered ❓ and ⛔ into 🔲, keeps ⚠️ and ❌; only /plan writes item text.
  2. build/SKILL.md: changes 🔲 to ✅; when stuck it leaves the plan as is, explains in chat and says "Run /plan".
  3. verify/SKILL.md: may edit only the Status line; on failure it leaves the plan as is and says "Run /plan".
  4. history/SKILL.md: skips tickets with no "Status:" line.
  5. CLAUDE.md and README.md: ❓ and ⛔ items replace the old sections; only ❓ and ⛔ stop /build.


✅ The tests cover the new structure (tests/workflow/test_validate_plan.py, tests/workflow/test_hooks.py, tests/workflow/test_precheck.py, tests/workflow/test_pr_link.py, tests/workflow/helpers.py)

  1. helpers.py: plan_text() builds a new-structure plan; new OLD_PLAN holds an old-structure sample.
  2. test_validate_plan.py: each mark, numbered changes, backticks rejected, the template is valid, old tickets skipped.
  3. test_precheck.py: /build refused on ❓ and ⛔, allowed with ⚠️ and ❌, old ticket counts as no plan.
  4. test_hooks.py: /build and /verify cannot add, remove or reword items.
  5. test_pr_link.py: goal() returns "" for OLD_PLAN.


✅ Every plan puts one blank line between an item and its changes and two blank lines between items, and the changes are short but technical (.claude/skills/plan/plan-template.md, .claude/skills/plan/SKILL.md, tests/workflow/test_validate_plan.py)

  1. plan-template.md: add one blank line after each item line, before its "1." change, and two blank lines after an item's last change, before the next item.
  2. plan/SKILL.md step 4: each change names the file, the function or field, and what changes, in a few words a junior developer understands, so the developer always knows which code will change.
  3. test_validate_plan.py: a plan with these blank lines is valid (parse() already skips blank lines).
