#!/usr/bin/env python3
"""Stop / StopFailure / SessionEnd: drop this session's authorization."""
from workflow_state import cleanup_stale, clear, read_input

data = read_input()
clear(data.get("session_id"))
if data.get("hook_event_name") == "SessionEnd":
    cleanup_stale()
