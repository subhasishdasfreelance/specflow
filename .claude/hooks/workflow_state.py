"""Per-session workflow mode, stored in .claude/runtime/<session_id>.json.

Missing, stale, mismatched or corrupt state always means 'analysis'.
"""
import json
import os
import re
import sys
import time
from pathlib import Path

MODES = ("analysis", "prd", "plan", "build", "verify", "vibe", "resolve")
# Slash command -> mode it authorizes.
COMMANDS = {"prd": "prd", "plan": "plan", "build": "build", "verify": "verify", "vibe": "vibe",
            "resolve-conflict": "resolve"}
MAX_AGE = 6 * 3600  # seconds; an authorization never outlives this
SID_RE = re.compile(r"^[A-Za-z0-9_-]{1,128}$")
ANALYSIS = {"mode": "analysis", "args": "", "prompt": ""}


def project_root():
    root = os.environ.get("CLAUDE_PROJECT_DIR") or Path(__file__).resolve().parents[2]
    return Path(os.path.realpath(root))


def runtime_dir():
    return project_root() / ".claude" / "runtime"


def read_input():
    try:
        data = json.load(sys.stdin)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def norm(text):
    return " ".join(str(text or "").split())


def _path(sid):
    if not isinstance(sid, str) or not SID_RE.match(sid):
        return None
    return runtime_dir() / f"{sid}.json"


def load(sid):
    path = _path(sid)
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return dict(ANALYSIS)
    now = time.time()
    created = state.get("created") if isinstance(state, dict) else None
    if (not isinstance(state, dict) or state.get("session_id") != sid
            or state.get("mode") not in MODES
            or not isinstance(created, (int, float))
            or not (now - MAX_AGE < created < now + 60)):
        return dict(ANALYSIS)
    return state


def save(sid, mode, args="", prompt=""):
    path = _path(sid)
    if path is None or mode not in MODES:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {"session_id": sid, "mode": mode, "args": norm(args),
            "prompt": norm(prompt), "created": time.time()}
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data), encoding="utf-8")
    os.replace(tmp, path)


def clear(sid):
    path = _path(sid)
    if path is not None:
        path.unlink(missing_ok=True)


def cleanup_stale():
    cutoff = time.time() - MAX_AGE
    for p in runtime_dir().glob("*.json"):
        try:
            if p.stat().st_mtime < cutoff:
                p.unlink()
        except OSError:
            pass
