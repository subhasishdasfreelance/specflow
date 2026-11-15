# feature/specit-append-guidelines

- Status: Human verified

## Goal
People who install specit keep their own files, and can cleanly remove what specit added.

## Todo
- [x] Installer downloads only `.claude/`, `README.md` and `guidelines.md`; saves the README as `README-specit.md`; leaves no `guidelines.md`; `~/.local/bin/specit` is unchanged. (specit)
- [x] Guidelines go at the end of `CLAUDE.md`, and ignore lines at the end of `.gitignore`, each between `specit:start`/`specit:end` markers; files are created if missing; existing text is kept; a re-run replaces the block. (specit)
- [x] Before "Proceed?", the installer lists every change; any answer but `y` changes nothing. (specit)
- [x] `README-specit.md` is renamed to `README.md`; Setup explains `specit` and what it adds; no `tests/workflow/` step. (README-specit.md, README.md)
- [x] Uninstall lists what was added and gives a copy-paste script without `rm -rf`; install then uninstall leaves the user's files as before. (README.md)
- [x] Tests run the installer and the README's uninstall script on a sample project. (tests/workflow/test_specit.py)

## Changes
1. Add `specit` at the repo root: a copy of `~/.local/bin/specit` that extracts `*/.claude`, `*/README.md`, `*/guidelines.md` into a `mktemp -d` folder.
2. In `specit`, copy `.claude/` into the project and `README.md` to `README-specit.md`.
3. In `specit`, an `add_block` function strips any old `start`..`end` block with `awk`, then appends the new one: guidelines to `CLAUDE.md` (`<!-- specit:start/end -->`), `.claude/runtime/` and `.claude/settings.local.json` to `.gitignore` (`# specit:start/end`).
4. In `specit`, the preview prints `new`/`overwrite` per file and `new`/`append`/`update` for `CLAUDE.md` and `.gitignore`.
5. `git mv README-specit.md README.md`; rewrite Setup (install steps + "what specit adds" table), Uninstall (removal list + bash block using `rm -f`, `rmdir`, `awk`) and Files.
6. Add `tests/workflow/test_specit.py`: build a tarball from tracked files, fake `curl` on `PATH`, run `specit` and the README's uninstall block, compare file snapshots.
