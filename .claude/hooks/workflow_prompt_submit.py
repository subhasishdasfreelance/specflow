#!/usr/bin/env python3
"""UserPromptSubmit: every new prompt starts in analysis mode.

Exception: if UserPromptExpansion already authorized *this exact prompt*
moments ago, keep it. This makes the result independent of hook order.
"""
import time

from workflow_state import cleanup_stale, clear, load, norm, read_input

data = read_input()
sid = data.get("session_id")
state = load(sid)
same_prompt = state["mode"] != "analysis" and state.get("prompt") == norm(data.get("prompt"))
if not (same_prompt and time.time() - state.get("created", 0) < 60):
    clear(sid)
cleanup_stale()
