#!/usr/bin/env python3
"""UserPromptExpansion: a user-typed workflow command (see COMMANDS)
authorizes its mode for this turn only. Nothing else can grant a mode."""
from workflow_state import COMMANDS, read_input, save

data = read_input()
name = str(data.get("command_name") or "").lstrip("/")
if data.get("expansion_type", "slash_command") == "slash_command" and name in COMMANDS:
    save(data.get("session_id"), COMMANDS[name], data.get("command_args") or "", data.get("prompt") or "")
