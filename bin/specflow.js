#!/usr/bin/env node
// Usage: specflow [--uninstall]
// Adds the specflow workflow to the current folder, or removes it again:
//   - copies .claude/, .github/workflows/specflow-plans.yml and README-specflow.md
//   - adds this package's CLAUDE.md to the end of CLAUDE.md and two lines to .gitignore,
//     each inside "specflow:start" / "specflow:end" markers (re-running replaces them)
//   - cleans up an old specit install and turns old 📝 todo marks into 🔲
"use strict";
const fs = require("fs");
const path = require("path");
const readline = require("readline");
const { spawnSync } = require("child_process");

const PKG = path.join(__dirname, "..");
const README = "README-specflow.md";
const MD_MARKERS = ["<!-- specflow:start -->", "<!-- specflow:end -->"];
const GI_MARKERS = ["# specflow:start", "# specflow:end"];
const GITIGNORE_LINES = ".claude/runtime/\n.claude/settings.local.json";
const OLD_README = "README-specit.md";
const OLD_MD_MARKERS = ["<!-- specit:start -->", "<!-- specit:end -->"];
const OLD_GI_MARKERS = ["# specit:start", "# specit:end"];
const OLD_MARK = "📝";
const NEW_MARK = "🔲";
const PYTHON_HINT = `specflow needs Python 3. Install it and make sure "python3 --version" works in a new terminal, then run specflow again.
On Windows, install Python from the Microsoft Store (it adds python3), or copy python.exe to python3.exe in the same folder.`;

// Files under root/dir, as "dir/..." paths with forward slashes.
function walk(root, dir) {
  return fs.readdirSync(path.join(root, dir), { withFileTypes: true }).flatMap((entry) => {
    const rel = `${dir}/${entry.name}`;
    return entry.isDirectory() ? walk(root, rel) : [rel];
  });
}

// The workflow files this package ships.
function listFiles() {
  return [...walk(PKG, ".claude"), ...walk(PKG, ".github")].sort();
}

// Tickets that still mark a todo with the old 📝.
function oldPlans() {
  if (!fs.existsSync("tickets")) return [];
  return walk(".", "tickets")
    .filter((f) => f.endsWith(".md") && lines(f).some((line) => line.startsWith(OLD_MARK)))
    .sort();
}

function lines(file) {
  return fs.readFileSync(file, "utf8").split("\n");
}

function hasLine(file, wanted) {
  return fs.existsSync(file) && lines(file).some((line) => line.replace(/\r$/, "") === wanted);
}

// What will happen to a file that gets a marked block: new, append or update.
function blockAction(file, start) {
  if (!fs.existsSync(file)) return "new";
  return hasLine(file, start) ? "update" : "append";
}

// Drop the lines from the start marker to the end marker.
function removeBlock(file, [start, end]) {
  if (!fs.existsSync(file)) return;
  let skip = false;
  const kept = lines(file).filter((line) => {
    const plain = line.replace(/\r$/, "");
    if (plain === start) skip = true;
    const keep = !skip;
    if (plain === end) skip = false;
    return keep;
  });
  fs.writeFileSync(file, kept.join("\n"));
}

// Remove the old marked block (if any), then add the new one at the end.
function addBlock(file, markers, text) {
  removeBlock(file, markers);
  let before = fs.existsSync(file) ? fs.readFileSync(file, "utf8") : "";
  if (before && !before.endsWith("\n")) before += "\n";
  fs.writeFileSync(file, `${before}${markers[0]}\n${text}\n${markers[1]}\n`);
}

// Remove the folders the package files live in, deepest first, each only when empty.
function removeEmptyDirs(files) {
  const dirs = new Set();
  for (const file of files) {
    for (let dir = path.posix.dirname(file); dir !== "."; dir = path.posix.dirname(dir)) dirs.add(dir);
  }
  const deepestFirst = [...dirs].sort((a, b) => b.split("/").length - a.split("/").length);
  for (const dir of deepestFirst) {
    if (fs.existsSync(dir) && fs.readdirSync(dir).length === 0) fs.rmdirSync(dir);
  }
}

function hasPython3() {
  const result = spawnSync("python3", ["--version"], { encoding: "utf8" });
  return result.status === 0 && /^Python 3\./.test(`${result.stdout}${result.stderr}`.trim());
}

function show(action, what) {
  console.log(`  ${action.padEnd(10)} ${what}`);
}

function ask(question) {
  const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
  return new Promise((resolve) => {
    rl.question(question, (answer) => {
      resolve(answer);
      rl.close();
    });
    rl.on("close", () => resolve(""));
  });
}

async function confirmed() {
  if ((await ask("Proceed? (y/N) ")).trim() === "y") return true;
  console.log("Cancelled.");
  return false;
}

async function install() {
  if (!hasPython3()) {
    console.error(PYTHON_HINT);
    process.exitCode = 1;
    return;
  }
  const files = listFiles();
  const plans = oldPlans();
  console.log(`Into: ${process.cwd()}`);
  for (const file of [...files, README]) show(fs.existsSync(file) ? "overwrite" : "new", file);
  show(blockAction("CLAUDE.md", MD_MARKERS[0]), "CLAUDE.md (workflow block)");
  show(blockAction(".gitignore", GI_MARKERS[0]), ".gitignore (specflow lines)");
  if (fs.existsSync(OLD_README)) show("remove", OLD_README);
  if (hasLine("CLAUDE.md", OLD_MD_MARKERS[0])) show("remove", "CLAUDE.md (old specit block)");
  if (hasLine(".gitignore", OLD_GI_MARKERS[0])) show("remove", ".gitignore (old specit lines)");
  for (const plan of plans) show("update", `${plan} (${OLD_MARK} to ${NEW_MARK})`);
  if (!(await confirmed())) return;

  for (const file of files) {
    fs.mkdirSync(path.dirname(file), { recursive: true });
    fs.copyFileSync(path.join(PKG, file), file);
  }
  fs.copyFileSync(path.join(PKG, "README.md"), README);
  fs.rmSync(OLD_README, { force: true });
  removeBlock("CLAUDE.md", OLD_MD_MARKERS);
  removeBlock(".gitignore", OLD_GI_MARKERS);
  const claudeBlock = fs.readFileSync(path.join(PKG, "CLAUDE.md"), "utf8").replace(/\n+$/, "");
  addBlock("CLAUDE.md", MD_MARKERS, claudeBlock);
  addBlock(".gitignore", GI_MARKERS, GITIGNORE_LINES);
  for (const plan of plans) {
    const marked = lines(plan).map((line) => (line.startsWith(OLD_MARK) ? NEW_MARK + line.slice(OLD_MARK.length) : line));
    fs.writeFileSync(plan, marked.join("\n"));
  }
  console.log("Done. Restart Claude Code and run /hooks.");
}

async function uninstall() {
  const files = listFiles();
  const present = [...files, README].filter((file) => fs.existsSync(file));
  const blocks = [["CLAUDE.md", MD_MARKERS], [".gitignore", GI_MARKERS]].filter(([file, markers]) => hasLine(file, markers[0]));
  for (const file of present) show("remove", file);
  for (const [file] of blocks) show("update", file);
  if (!(await confirmed())) return;

  for (const file of present) fs.rmSync(file);
  for (const dir of [".claude/runtime", ".claude/hooks/__pycache__", ".claude/scripts/__pycache__"]) {
    fs.rmSync(dir, { recursive: true, force: true });
  }
  removeEmptyDirs(files);
  for (const [file, markers] of blocks) {
    removeBlock(file, markers);
    if (fs.readFileSync(file, "utf8") === "") fs.rmSync(file);
  }
  console.log("Done. Restart Claude Code and check /hooks lists no workflow hooks.");
}

function main(args) {
  if (args.length === 0) return install();
  if (args.length === 1 && args[0] === "--uninstall") return uninstall();
  console.error("Usage: specflow [--uninstall]");
  process.exitCode = 1;
}

main(process.argv.slice(2));
