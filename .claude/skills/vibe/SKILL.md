---
name: vibe
description: Explicitly authorize an ad-hoc code change outside the plan.
disable-model-invocation: true
argument-hint: "<what to change>"
---

Request: `$ARGUMENTS`

Name the branch. If the request is unclear, ask and stop. Otherwise make the smallest change that does this, following CLAUDE.md › Code. Test it.
Reply in a few lines: files changed, how you checked it, and any divergence from `tickets/` (suggest `/plan revise` if scope changed).
Don't edit the PRD or tickets. No commits.
