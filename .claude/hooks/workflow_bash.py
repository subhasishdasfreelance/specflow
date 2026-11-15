"""Bash policy. Returns a deny reason (str) or None.

Read-only modes (analysis, prd, plan, verify, complete) use an allowlist.
Write modes (build, vibe) block destructive git, protected paths and
dangerous deletes. This is a best-effort parser, not a sandbox.
"""
import glob
import os
import re
import shlex

from workflow_policy import active_build, classify, contains_protected, resolve, source_write

SEPS = {";", "&&", "||", "|", "&", "|&", "(", ")", ";;", ";&", "{", "}"}
WRITE_REDIRS = {">", ">>", ">|", "&>", "&>>", ">&"}
READ_REDIRS = {"<", "<<", "<<<", "<<-", "<&"}
READ_ONLY = {"ls", "cat", "head", "tail", "wc", "grep", "egrep", "fgrep", "rg", "pwd",
             "echo", "printf", "file", "stat", "du", "df", "which", "type", "whoami",
             "date", "uname", "cut", "tr", "uniq", "diff", "cmp", "basename", "dirname",
             "realpath", "readlink", "jq", "cd", "true", "false", "test", "[", "tree",
             "sort", "find", "nl", "column", "comm", "sha256sum", "md5sum"}
NEVER = {"sudo", "su", "doas", "eval", "source", ".", "dd", "mkfs", "shutdown",
         "reboot", "crontab", "exec"}
WRAPPERS = {"env", "nohup", "time", "nice", "command", "timeout", "stdbuf", "xargs"}
SHELLS = {"bash", "sh", "zsh", "dash"}
DESTRUCTIVE = {"rm", "rmdir", "mv", "cp", "chmod", "chown", "ln", "rsync",
               "truncate", "shred", "install", "unlink"}
FIND_WRITE = {"-delete", "-exec", "-execdir", "-ok", "-okdir", "-fprint", "-fprint0",
              "-fprintf", "-fls"}
GIT_READ = {"status", "log", "diff", "show", "rev-parse", "ls-files", "ls-tree",
            "merge-base", "blame", "shortlog", "describe", "cat-file", "rev-list",
            "grep", "for-each-ref", "name-rev", "show-ref", "count-objects", "version"}
BRANCH_WRITE = {"-d", "-D", "--delete", "-m", "-M", "--move", "-c", "-C", "--copy",
                "-f", "--force", "-u", "--set-upstream-to", "--unset-upstream",
                "--edit-description"}
GH_READ = {("pr", "view"), ("pr", "list"), ("pr", "status"), ("pr", "diff"),
           ("pr", "checks"), ("repo", "view"), ("auth", "status"),
           ("issue", "view"), ("issue", "list")}
# What each mode may do with git / gh, beyond plain reads.
GIT_ALLOWED = {
    "analysis": {"read"}, "prd": {"read"}, "plan": {"read"}, "verify": {"read"},
    "build": {"read", "branch", "stage"}, "vibe": {"read", "branch", "stage"},
    "complete": {"read", "branch", "stage", "commit", "push", "pr-create"},
    "resolve": {"read", "stage", "commit", "merge"},
}
SCRIPT_OK = re.compile(r"^(test|lint|typecheck|type-check|check|build)(:|$)")
GRADLE_OK = re.compile(r"^(:?[\w-]+:)*(test|lint|check|build|assemble)\w*$", re.I)
FIX_FLAGS = {"--fix", "--write", "-w", "-u", "--update", "--updateSnapshot",
             "--update-snapshots"}
PROTECTED_TEXT = (".claude/", ".claude\\", "CLAUDE.md", "docs/PRD.md", "docs/tickets", ".git/")


def tokenize(cmd):
    lex = shlex.shlex(cmd.replace("\n", " ; "), posix=True, punctuation_chars=True)
    lex.whitespace_split = True
    return list(lex)


def segments(tokens):
    """Split tokens into commands: list of (words, [(redir_op, target)])."""
    out, words, redirs, i = [], [], [], 0
    while i < len(tokens):
        t = tokens[i]
        if t in SEPS:
            out.append((words, redirs))
            words, redirs = [], []
        elif t in WRITE_REDIRS or t in READ_REDIRS:
            target = tokens[i + 1] if i + 1 < len(tokens) else ""
            redirs.append((t, target))
            i += 1
        elif t != "$":
            words.append(t)
        i += 1
    out.append((words, redirs))
    return [(w, r) for w, r in out if w or r]


def strip_wrappers(words):
    while words and (re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", words[0]) or words[0] in WRAPPERS):
        words = words[1:]
        while words and (words[0].startswith("-") or re.match(r"^[\w.]+=|^\d+[smh]?$", words[0])):
            words = words[1:]
    return words


def is_validator(words):
    return (len(words) >= 2 and os.path.basename(words[0]) in ("python", "python3")
            and words[1].replace("\\", "/").endswith(".claude/scripts/validate_plan.py"))


def git_kind(words):
    args = words[1:]
    while args and args[0].startswith("-"):
        if args[0] == "-C" and len(args) > 1:
            args = args[2:]
        elif args[0] in ("--no-pager", "-P", "--no-optional-locks"):
            args = args[1:]
        else:
            return "other"
    if not args:
        return "read"
    sub, rest = args[0], args[1:]
    flags = [r for r in rest if r.startswith("-")]
    pos = [r for r in rest if not r.startswith("-")]
    if any(r.startswith("--output") for r in rest):
        return "other"
    if sub in GIT_READ:
        return "read"
    if sub == "branch":
        if set(flags) & BRANCH_WRITE:
            return "other"
        listing = {"--contains", "--no-contains", "--merged", "--no-merged", "--list", "-l"}
        return "branch" if pos and not set(flags) & listing else "read"
    if sub == "tag":
        return "read" if not pos or set(flags) & {"-l", "--list"} else "other"
    if sub == "remote":
        return "read" if not pos or pos[0] in ("show", "get-url") else "other"
    if sub == "config":
        return "read" if set(flags) & {"--get", "--list", "-l", "--get-all", "--get-regexp"} else "other"
    if sub == "stash":
        return "read" if pos[:1] in (["list"], ["show"]) else "other"
    if sub == "checkout":
        if "-b" in flags:
            return "branch"
        return "merge" if set(flags) & {"--ours", "--theirs"} else "other"
    if sub == "pull":
        return "other" if any(f in ("-r", "--force") or f.startswith("--rebase") for f in flags) else "merge"
    if sub in ("fetch", "merge"):
        return "other" if "--force" in flags or "-f" in flags else "merge"
    if sub == "switch":
        return "branch" if set(flags) & {"-c", "--create"} else "other"
    if sub in ("add", "mv", "rm"):
        return "stage"
    if sub == "commit":
        return "other" if "--amend" in flags else "commit"
    if sub == "push":
        bad = [r for r in rest if r.startswith(("--force", "+", ":"))
               or r in ("-f", "-d", "--delete", "--mirror", "--all", "--prune", "--tags")]
        return "other" if bad else "push"
    return "other"


def gh_kind(words):
    pair = tuple(w for w in words[1:3])
    if pair in GH_READ:
        return "read"
    return "pr-create" if pair == ("pr", "create") else "other"


def is_read_only(words):
    cmd = os.path.basename(words[0])
    if len(words) == 2 and words[1] in ("--version", "-V", "version"):
        return True
    if cmd == "find":
        return not set(words) & FIND_WRITE
    if cmd == "sort":
        return not any(w.startswith(("-o", "--output")) for w in words)
    if cmd == "git":
        return git_kind(words) == "read"
    if cmd == "gh":
        return gh_kind(words) == "read"
    return cmd in READ_ONLY or is_validator(words)


def is_check_command(words):
    """Test / lint / build commands that /verify may run (no fix flags)."""
    if set(words) & FIX_FLAGS:
        return False
    cmd, rest = os.path.basename(words[0]), words[1:]
    first = rest[0] if rest else ""
    if cmd in ("npm", "pnpm", "yarn", "bun"):
        if first == "exec":
            return bool(rest[1:]) and is_check_command(rest[1:])
        script = rest[1] if first == "run" and len(rest) > 1 else first
        return script == "t" or bool(SCRIPT_OK.match(script))
    if cmd in ("npx", "bunx"):
        return bool(rest) and is_check_command(rest)
    if cmd in ("python", "python3"):
        return first == "-m" and len(rest) > 1 and rest[1] in (
            "pytest", "unittest", "mypy", "pyright", "flake8", "pylint", "bandit")
    if cmd in ("pytest", "mypy", "pyright", "flake8", "pylint", "bandit", "tsc",
               "eslint", "vitest", "jest", "playwright"):
        return True
    if cmd == "ruff":
        return first == "check" or (first == "format" and "--check" in rest)
    if cmd == "prettier":
        return "--check" in rest
    if cmd in ("gradle", "gradlew"):  # Android/JVM: test, lint, check, build, assembleDebug...
        return bool(rest) and all(GRADLE_OK.match(w) for w in rest if not w.startswith("-"))
    table = {"go": {"test", "vet", "build"}, "cargo": {"test", "check", "clippy", "build"},
             "make": {"test", "check", "lint", "build", "typecheck"},
             "mvn": {"test", "verify", "compile"}, "mvnw": {"test", "verify", "compile"},
             "dotnet": {"test", "build"}, "swift": {"test", "build"},
             "flutter": {"test", "analyze"}, "dart": {"test", "analyze"}}
    return first in table.get(cmd, set())


def redirect_error(mode, op, target, cwd):
    if op not in WRITE_REDIRS or target == "/dev/null" or (op == ">&" and target.isdigit()):
        return None
    kind = classify(resolve(target, cwd))
    if kind == "scratch":
        return None
    if mode in ("build", "vibe") and kind == "source":
        return source_write(mode)
    return f"{mode} mode: redirecting output to '{target}' is not allowed."


def path_error(words, cwd):
    """Write-mode checks on a non-read-only command's arguments."""
    cmd = os.path.basename(words[0])
    for w in words[1:]:
        if any(p in w for p in PROTECTED_TEXT):
            return f"'{cmd}' touches protected workflow files or docs (use /prd, /plan or the Edit tool)."
        if w.startswith("-"):
            continue
        paths = glob.glob(os.path.join(cwd, w)) if re.search(r"[*?[]", w) else [w]
        for p in paths:
            path = resolve(p, cwd)
            kind = classify(path)
            if kind in ("protected", "prd", "plan"):
                return f"'{cmd}' touches protected workflow files or docs."
            if cmd in DESTRUCTIVE and (kind in ("root", "outside") or contains_protected(path)):
                return f"'{cmd}' on '{w}' (project root or outside the project) is blocked."
    return None


def segment_error(mode, args, words, cwd, depth):
    words = strip_wrappers(words)
    if not words:
        return None
    cmd = os.path.basename(words[0])
    if is_validator(words):
        return None
    if cmd in NEVER:
        return f"'{cmd}' is never allowed by the workflow."
    if cmd in SHELLS and "-c" in words:
        i = words.index("-c")
        return bash_decision(mode, args, words[i + 1] if i + 1 < len(words) else "", cwd, depth + 1)
    if cmd in ("git", "gh"):
        kind = git_kind(words) if cmd == "git" else gh_kind(words)
        if kind not in GIT_ALLOWED[mode]:
            return f"{mode} mode: '{' '.join(words[:3])}' is not allowed. Commits, pushes and PRs belong to /complete; merges to /resolve-conflict."
        if kind == "push" and args.split()[:1]:
            base = args.split()[0]
            if any(w == base or w.endswith(":" + base) for w in words[2:]):
                return f"Pushing directly to the base branch '{base}' is not allowed."
        return None
    if is_read_only(words):
        return None
    if mode in ("verify", "resolve") and is_check_command(words):
        return None
    if mode in ("build", "vibe"):
        if cmd in ("python", "python3") and words[1:2] and words[1].replace("\\", "/").startswith(".claude"):
            return "Running workflow internals is not allowed."
        return path_error(words, cwd) or (source_write(mode) if mode == "build" else None)
    return f"{mode} mode: '{cmd}' is not a read-only command. Use /vibe or /build to change code."


def bash_decision(mode, args, command, cwd, depth=0):
    if depth > 3:
        return "Command nesting too deep."
    if mode == "build" and not active_build():
        mode = "analysis"  # build without a Building plan gets read-only rights
    read_only_mode = mode not in ("build", "vibe")
    if "`" in command or (read_only_mode and re.search(r"[$<>]\(", command)):
        return f"{mode} mode: command substitution is not allowed here."
    try:
        segs = segments(tokenize(command))
    except ValueError:
        return "Could not parse command (unbalanced quotes)."
    for words, redirs in segs:
        for op, target in redirs:
            err = redirect_error(mode, op, target, cwd)
            if err:
                return err
        if words and os.path.basename(words[0]) == "cd" and len(words) > 1:
            cwd = resolve(words[1], cwd)
            continue
        err = segment_error(mode, args, words, cwd, depth)
        if err:
            return err
    return None
