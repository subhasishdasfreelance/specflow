feature/npx-script
Status: Verified (Skipped)

Goal:
Anyone can add, update or remove the specflow workflow in any project on Windows, macOS or Linux with npx specflow or bunx specflow, with no bash, curl or GitHub token, an old specit install is cleaned up on the way, plan todos are marked 🔲 instead of 📝 (old plans too), GitHub Actions fails on every push while any plan is not Verified, except plans you mark Verified (Skipped), specit is renamed to specflow everywhere, past tickets included, and bun run release:<kind> "message" makes a release from a clean main.

Todo:
✅ The repo is a public, MIT-licensed npm package named specflow, version 0.1.0, that ships only the workflow files (package.json, LICENSE)

  1. package.json: name "specflow", version "0.1.0", a one-line description, license "MIT", bin { "specflow": "bin/specflow.js" }, engines node ">=18".
  2. package.json files: "bin", ".claude/hooks/*.py", ".claude/scripts/*.py", ".claude/skills/**/*.md", ".claude/settings.json", "CLAUDE.md". npm adds README.md, LICENSE and package.json by itself, so .claude/runtime, settings.local.json, __pycache__, tickets and tests stay out.
  3. package.json repository: git+https://github.com/subhasishdasfreelance/specflow.git.
  4. LICENSE: the standard MIT license text, "Copyright (c) 2026 Subhasish Das".


✅ npx specflow stops before changing anything when python3 is missing, and says how to fix it (bin/specflow.js)

  1. bin/specflow.js checkPython3: run "python3 --version" with child_process.spawnSync. It passes only when it exits 0 and prints "Python 3.".
  2. On failure print: specflow needs Python 3; install it and make sure python3 --version works in a new terminal, then run specflow again; on Windows install Python from the Microsoft Store (it adds python3) or copy python.exe to python3.exe in the same folder.
  3. main: run the check before install only, not for --uninstall, and exit with code 1 when it fails.


✅ npx specflow lists every change, asks "Proceed? (y/N)", and only on y adds the same files and blocks the bash script did (bin/specflow.js)

  1. bin/specflow.js top: shebang #!/usr/bin/env node, and only node built-ins (fs, path, readline, child_process) so it also runs under bunx.
  2. PKG is the folder above bin (path.join(__dirname, "..")). listFiles walks PKG/.claude and returns sorted paths with forward slashes.
  3. blockAction(file, start): "new" if the file is missing, "update" if a line equals the start marker, else "append".
  4. addBlock(file, start, end, text): drop the old lines from the start marker to the end marker, then append start, text and end, each ending in a newline.
  5. Install preview: print "Into: <current folder>", then "  new        <file>" or "  overwrite  <file>" for each .claude file and README-specflow.md, then the "CLAUDE.md (workflow block)" and ".gitignore (specflow lines)" lines, same layout as today.
  6. Ask "Proceed? (y/N) " with readline. Anything but y prints "Cancelled." and exits 0.
  7. On y: copy the PKG/.claude files in (same names are overwritten) and PKG/README.md to README-specflow.md.
  8. On y: add the CLAUDE.md block (<!-- specflow:start --> and <!-- specflow:end --> around PKG/CLAUDE.md) and the .gitignore block (# specflow:start and # specflow:end around .claude/runtime/ and .claude/settings.local.json), then print "Done. Restart Claude Code and run /hooks."
  9. main: no argument installs, --uninstall uninstalls, any other argument prints "Usage: specflow [--uninstall]" and exits 1.


✅ npx specflow also removes what an old specit install left behind, so no block is doubled (bin/specflow.js)

  1. removeBlock(file, start, end): drop the lines from the start marker to the end marker; shared with uninstall.
  2. Install preview: add "  remove     README-specit.md" when it exists, and "  remove     CLAUDE.md (old specit block)" or ".gitignore (old specit lines)" when a specit:start marker is there.
  3. On y, before adding the new blocks: delete README-specit.md, and removeBlock the <!-- specit:start --> / <!-- specit:end --> block from CLAUDE.md and the # specit:start / # specit:end block from .gitignore.
  4. The .claude files of the old install have the same names and are simply overwritten.


✅ npx specflow --uninstall removes only what specflow added and keeps anything that still holds the user's own content (bin/specflow.js)

  1. Uninstall preview: print "  remove     <file>" for each existing file from listFiles plus README-specflow.md, and "  update     CLAUDE.md" or ".gitignore" when its block is there. Then ask "Proceed? (y/N) " like install.
  2. On y: delete those files, .claude/runtime, and the __pycache__ folders in .claude/hooks and .claude/scripts.
  3. removeEmptyDirs: remove each skill folder, then .claude/skills, .claude/hooks, .claude/scripts and .claude, each only when empty.
  4. removeBlock the specflow block from CLAUDE.md and .gitignore, and delete the file if nothing is left.
  5. Print "Done. Restart Claude Code and check /hooks lists no workflow hooks."


✅ The bash specit script is gone (specit)

  1. specit: delete the file.


✅ Installer tests run the packed npm package and pass on Windows, macOS and Linux (tests/workflow/test_specit.py renamed to tests/workflow/test_specflow.py)

  1. Rename tests/workflow/test_specit.py to tests/workflow/test_specflow.py and update its docstring.
  2. setUpClass: run npm pack --pack-destination <tmp> in REPO once (find npm with shutil.which so npm.cmd works on Windows), unpack the .tgz with tarfile, and keep the path to package/bin/specflow.js.
  3. setUp: drop FAKE_CURL, the fake bin folder, the GitHub-style tarball and GITHUB_TOKEN. Use a copy of os.environ.
  4. install(answer) runs node with the packed bin/specflow.js; uninstall() runs it with --uninstall and answers y.
  5. Drop uninstall_script and the re and textwrap imports only it used.
  6. test_fresh_project and test_existing_files_kept_and_rerun_replaces_block: expect specflow markers and README-specflow.md, and check that no __pycache__ or runtime folder is copied.
  7. New test_missing_python3_stops: run node by its full path with PATH set to an empty temp folder (keep SYSTEMROOT for Windows). Expect exit code 1, "python3" in the output, and the project unchanged.
  8. Keep test_answer_no_changes_nothing.
  9. New test_old_specit_install_cleaned_up: start with a CLAUDE.md and .gitignore holding specit blocks plus README-specit.md; after install expect no specit:start left, one specflow block each, the user's own lines kept, and no README-specit.md.


✅ All tests run on Windows, macOS and Linux on every push (.github/workflows/test.yml)

  1. .github/workflows/test.yml: on push, matrix os ubuntu-latest, macos-latest and windows-latest.
  2. Steps: actions/checkout, actions/setup-python with 3.x, actions/setup-node with 20.
  3. Windows only: if python3 is missing, copy python.exe to python3.exe in the same folder, the same fix the installer suggests.
  4. Run python -m unittest discover -s tests/workflow -t tests/workflow.


✅ Pushing an annotated tag like v0.1.1 publishes that version to npm (.github/workflows/publish.yml)

  1. .github/workflows/publish.yml: on push of tags matching v*, runs on ubuntu-latest, permissions id-token: write and contents: read.
  2. Steps: actions/checkout, actions/setup-node with 24 and registry-url https://registry.npmjs.org.
  3. Fail if the tag is not "v" plus the version in package.json.
  4. Run npm publish through npm trusted publishing, so no token secret is needed.


⚠️ The first publish (0.1.0) is manual, because trusted publishing can only be set up on npmjs.com once the package exists

  1. After merging to main: git tag -a v0.1.0 -m "Release 0.1.0", git push --follow-tags, npm publish --access public.
  2. The publish workflow run for v0.1.0 fails because that version is already on npm. That is expected.
  3. Then on npmjs.com, package specflow, Settings, Trusted Publisher: GitHub Actions, subhasishdasfreelance/specflow, publish.yml.


⚠️ You rename the GitHub repo to specflow before the first publish

  1. package.json repository and the npm trusted publisher both point at subhasishdasfreelance/specflow.


❌ No release-it: releases use this repo's own release scripts, and publish.yml publishes

  1. No release-it dependency or config in package.json.


✅ bun run release:patch "message" (or minor, major, alpha, beta) bumps the version, commits, creates an annotated tag with that message and pushes both, only from a clean main and only with a message (package.json, scripts/release.js)

  1. package.json scripts: release:patch, release:minor, release:major, release:alpha and release:beta, each runs "node scripts/release.js <kind>".
  2. scripts/release.js main: the kind is the first argument; the message is the rest, joined by spaces and trimmed. No message: print Usage: bun run release:<kind> "message" and exit 1.
  3. Exit 1 with a clear message unless git branch --show-current prints main.
  4. Exit 1 with a clear message if git status --porcelain prints anything, so staged, unstaged and untracked files all stop it.
  5. nextVersion(current, kind), like npm version: patch 0.1.0 to 0.1.1, minor to 0.2.0, major to 1.0.0. From a prerelease, patch, minor or major first drop the -alpha.n or -beta.n part, and bump only if the lower parts are not already zero (0.2.0-beta.1 with minor becomes 0.2.0).
  6. nextVersion alpha and beta from a stable version start at the next minor: 0.1.0 becomes 0.2.0-alpha.0 or 0.2.0-beta.0.
  7. nextVersion alpha: 0.2.0-alpha.0 to 0.2.0-alpha.1. beta: 0.2.0-alpha.1 to 0.2.0-beta.0, and 0.2.0-beta.0 to 0.2.0-beta.1. alpha on a beta version exits 1 (no going back).
  8. Write the new version into package.json, keeping its 2-space layout and final newline.
  9. Run git add package.json, git commit -m <message>, git tag -a v<new> -m <message>, git push --follow-tags origin main. Stop at the first git command that fails and show its error.
  10. Print "Released v<new>. The publish workflow puts it on npm."
  11. Only node built-ins and git, so it works the same from bun or npm (npm run release:minor -- "message") on Windows, macOS and Linux. scripts/ is not in package.json files, so it is not shipped.


✅ The release script is tested in a throwaway git repo (tests/workflow/test_release.py)

  1. setUp: a temp git repo on main with a package.json at 0.1.0 and a copy of scripts/release.js, plus a bare repo as its origin.
  2. test_refuses: no message, a branch other than main, a changed file and an untracked file each exit 1, with no new commit or tag.
  3. test_minor_release: release minor "added new option to check history" gives package.json 0.2.0, a commit with that message, an annotated tag v0.2.0 with that message (git cat-file -t v0.2.0 prints tag), and both on the bare origin.
  4. test_prerelease_steps: from 0.1.0, alpha, alpha, beta, then minor give 0.2.0-alpha.0, 0.2.0-alpha.1, 0.2.0-beta.0, then 0.2.0; alpha on 0.2.0-beta.0 exits 1.


✅ publish.yml puts alpha and beta versions under their own npm tag, so npx specflow keeps getting the latest stable version (.github/workflows/publish.yml)

  1. Publish step: a version with -alpha. runs npm publish --tag alpha, one with -beta. runs npm publish --tag beta, any other runs npm publish.


✅ The README Releasing section describes the release scripts (README.md)

  1. README.md Releasing: on main with nothing uncommitted, run bun run release:patch "what changed" (or minor, major, alpha, beta; with npm: npm run release:patch -- "what changed"). It bumps, commits, tags and pushes; the publish workflow puts it on npm.
  2. Add: try a prerelease with npx specflow@alpha or npx specflow@beta.


⚠️ The release push fails if main on GitHub is ahead of yours or only accepts pull requests

  1. Run git pull first. If main is protected, run /plan again for a release-from-PR flow.


✅ The README describes specflow, install and uninstall with npx or bunx, and how to release (README.md)

  1. README.md title: "specflow: plan first, code second", and every specit becomes specflow.
  2. Setup: needs Claude Code, Python 3 (python3 --version must work), git, and Node 18+ or Bun. Run npx specflow or bunx specflow; pin a version with npx specflow@0.1.0. Drop the PATH, chmod and GITHUB_TOKEN steps.
  3. "specflow adds" table: README-specflow.md and the specflow:start / specflow:end markers.
  4. Uninstall: replace the bash block with npx specflow --uninstall (or bunx specflow --uninstall). Keep the notes on settings.json, docs/PRD.md, tickets/ and /hooks.
  5. Limits: replace "Bash only (no PowerShell). Tested on Linux." with: Claude Code must use Bash (Git Bash on Windows) because the hooks block PowerShell; tests run on Linux, macOS and Windows.
  6. New "Releasing" section; its text is set by the release scripts todo below.
  7. Good to know: running the workflow's tests also needs Node, for npm pack.
  8. Last line: this repo also holds bin/specflow.js (the installer), package.json, .github/workflows/test.yml and publish.yml, and tests/workflow, which aren't installed.
  9. "specflow adds" table: a row for .github/workflows/specflow-plans.yml, a GitHub check that fails while any plan is not Verified; other workflow files are never touched.
  10. Good to know, "Check plans" line: add that --verified also fails unless every plan is Verified, as the GitHub check does.


✅ Plans mark an open todo with 🔲 instead of ▢, and the validator, hooks, skills, README and tests all use 🔲 (validate_plan.py, workflow_policy.py, plan and build skills, README.md, tests)

  1. .claude/scripts/validate_plan.py: TODO becomes "🔲", and the first choice in ITEM_RE becomes 🔲 instead of ▢.
  2. .claude/hooks/workflow_policy.py: normalize docstring and the "may only change the Status line" message say 🔲 -> ✅.
  3. .claude/skills/plan/plan-template.md: the todo line starts with 🔲.
  4. .claude/skills/plan/SKILL.md step 2: answered ❓ and ⛔ items become 🔲 todos.
  5. .claude/skills/build/SKILL.md: work through the 🔲 todos, and change each 🔲 to ✅ when done.
  6. README.md: the /plan and /build rows and the marks list say 🔲 todo.
  7. tests/workflow/helpers.py plan_text, test_validate_plan.py and test_hooks.py: every ▢ becomes 🔲, including the expected error texts.
  8. The validator accepts only 🔲. test_old_mark_is_not_a_todo checks that lines starting with 📝 or ▢ are not items.
  9. Build this todo last: this ticket still uses ▢ until then, and the new validator only accepts 🔲.


✅ Old plans use 🔲 too: npx specflow converts 📝 todos, and this repo's past tickets are updated (bin/specflow.js, tests/workflow/test_specflow.py, tickets/feature/simpler-plan.md)

  1. bin/specflow.js: NEW_MARK becomes "🔲". oldPlans still lists the .md files under tickets/ that have a line starting with 📝. ▢ was never released, so it is not converted.
  2. Install preview: print "  update     tickets/<name>.md (📝 to 🔲)" for each of them.
  3. On y: in each of them, replace the 📝 at the start of a line with 🔲. 📝 anywhere else in the text stays.
  4. tests/workflow/test_specflow.py test_old_plans_get_new_mark: expect the item to start with 🔲 and the preview to say (📝 to 🔲); the sentence stays unchanged.
  5. tickets/feature/simpler-plan.md: replace every ▢ with 🔲, so it matches the current mark.


✅ Past tickets say specflow instead of specit, file names included (tickets/feature/simpler-plan.md, updated-instructions.md, specit-append-guidelines.md)

  1. tickets/feature/simpler-plan.md and updated-instructions.md: replace every specit with specflow, for example README-specit.md becomes README-specflow.md.
  2. Rename tickets/feature/specit-append-guidelines.md to tickets/feature/specflow-append-guidelines.md, and change its first line to feature/specflow-append-guidelines.
  3. In that file, replace every other specit with specflow too.
  4. Check: git grep -i specit finds the word only in bin/specflow.js, tests/workflow/test_specflow.py and this ticket, where it names the old install that gets cleaned up.


⚠️ The renamed old ticket no longer matches its git branch, feature/specit-append-guidelines

  1. That branch is already merged, and the ticket is in the old structure, so no command looks it up by branch.


✅ validate_plan.py --verified fails when any plan is not exactly Verified, and skips plans marked Verified (Skipped) (.claude/scripts/validate_plan.py, tests/workflow/test_validate_plan.py)

  1. validate_plan.py main: a --verified flag. With it, each plan must pass validate() and its status must equal "Verified", else print "FAIL <path>" and below it "  - status is '<status>', must be 'Verified'", the same layout as the other errors, and exit 1.
  2. validate_plan.py: new SKIPPED = "Verified (Skipped)", added to STATUSES so the plain check accepts it. It is not in DONE, so open todos may remain.
  3. --verified: a plan whose status equals SKIPPED is not checked at all; print "SKIP <path>" and move on.
  4. --verified without file names checks every plan in tickets/, like today. Old-structure tickets are still skipped.
  5. validate_plan.py docstring: add the --verified usage line and that Verified (Skipped) plans are skipped.
  6. test_validate_plan.py new test_verified_flag: passes when all plans are Verified or Verified (Skipped), even with a broken skipped plan; fails for Verified (not human-verified), Building and Built.


✅ Only you can set Verified (Skipped); /plan, /build and /verify can't (README.md, tests/workflow/test_hooks.py)

  1. No hook change: the hooks already let /build and /verify set only their own statuses, and /plan only the unverified ones.
  2. test_hooks.py test_verify_sets_claude_verified_only: add ("Built", "Verified (Skipped)") to the denied list.
  3. README.md Statuses: add "Verified (Skipped): set it by hand on a plan you won't finish or verify; the plan check skips it."


✅ On every push, GitHub Actions fails when any plan is not Verified (.github/workflows/specflow-plans.yml)

  1. .github/workflows/specflow-plans.yml: name "specflow plans", on push (every branch), one job on ubuntu-latest.
  2. Steps: actions/checkout, then python3 .claude/scripts/validate_plan.py --verified.
  3. It is a file of its own, so it runs next to any workflows a project already has and never changes them.


⚠️ A branch whose plan is still being worked on shows a red check until that plan is Verified

  1. This is expected; mark a plan Verified (Skipped) to leave it out.


✅ npx specflow adds and removes the plan check without touching other workflow files (bin/specflow.js, package.json, tests/workflow/test_specflow.py)

  1. package.json files: add ".github/workflows/specflow-plans.yml". test.yml and publish.yml stay out of the package.
  2. bin/specflow.js listFiles: also list PKG/.github, so the preview, install and uninstall cover specflow-plans.yml like the .claude files.
  3. Install: create .github/workflows if missing and copy only specflow-plans.yml; other files in that folder are never read or changed.
  4. removeEmptyDirs: after removing specflow-plans.yml, also remove .github/workflows and .github, each only when empty.
  5. test_specflow.py new test_existing_workflows_untouched: a project with .github/workflows/ci.yml; after install ci.yml is byte for byte the same and specflow-plans.yml exists; after uninstall only ci.yml is left.


✅ npx specflow keeps its blocks on their own lines when CLAUDE.md or .gitignore doesn't end with a newline, so running it again never doubles a block (bin/specflow.js, tests/workflow/test_specflow.py)

  1. bin/specflow.js addBlock: when the file has text that doesn't end with a newline, write a newline before the start marker.
  2. After uninstall, that file's last line keeps the added newline.
  3. tests/workflow/test_specflow.py new test_file_without_trailing_newline: .gitignore holds "node_modules/" with no newline; after two installs the first line is "node_modules/" and there is one specflow block; after uninstall the file is "node_modules/" plus a newline.


⚠️ The plan check fails in this repo until you sign off the open plans

  1. tickets/feature/updated-instructions.md is Verified (not human-verified); this ticket is not Verified yet.
  2. Delete the notes in brackets after testing, as usual. tickets/feature/specflow-append-guidelines.md is old structure and is skipped.


⚠️ /build can edit .claude/ only while hooks are off here, because the hooks protect it

  1. Put { "disableAllHooks": true } in .claude/settings.local.json before /build, and delete it afterwards.


⚠️ The hook tests have only run on Linux so far

  1. If they fail on Windows or macOS in CI, run /plan again to fix them.
