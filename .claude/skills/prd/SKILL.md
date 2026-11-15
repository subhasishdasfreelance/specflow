---
name: prd
description: Create or update docs/PRD.md from requirements, even vague ones.
disable-model-invocation: true
argument-hint: "<requirements, answers, or a change>"
---

Input: `$ARGUMENTS` plus this conversation. Write only `docs/PRD.md`. Never code, never tickets.

1. Read the existing PRD (if any) and skim the repo to learn the platform and stack.
2. List what is unclear or missing: users, goals, scope, platforms, integrations, constraints. If anything that shapes the product is unclear, ask numbered questions (offer options where helpful) and stop. Say "Answer with `/prd <answers>`." Never fill gaps with guesses.
3. Write or update the PRD from [prd-template.md](prd-template.md). Keep it short and product-level: no stories, tasks or history (git tracks changes). Minor unknowns go to Open questions.
4. Reply in 2-3 lines. Then "Next: describe a feature, then `/plan <branch>`."
