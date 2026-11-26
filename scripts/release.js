// Usage: node scripts/release.js <patch|minor|major|alpha|beta> <message>
// From a clean main: bumps package.json, commits, creates the annotated tag v<version>
// with the message, and pushes both. The publish workflow then puts it on npm.
"use strict";
const fs = require("fs");
const { spawnSync } = require("child_process");

const KINDS = ["patch", "minor", "major", "alpha", "beta"];

function fail(message) {
  console.error(message);
  process.exit(1);
}

function git(...args) {
  const result = spawnSync("git", args, { encoding: "utf8" });
  if (result.status !== 0) fail(`git ${args.join(" ")} failed:\n${result.stderr || result.stdout}`);
  return result.stdout.trim();
}

// Like npm version; alpha and beta from a stable version start at the next minor.
function nextVersion(current, kind) {
  const match = /^(\d+)\.(\d+)\.(\d+)(?:-(alpha|beta)\.(\d+))?$/.exec(current);
  if (!match) fail(`Can't bump version ${current}.`);
  const [major, minor, patch] = match.slice(1, 4).map(Number);
  const pre = match[4];
  const preNumber = Number(match[5]);
  if (kind === "patch") return pre ? `${major}.${minor}.${patch}` : `${major}.${minor}.${patch + 1}`;
  if (kind === "minor") return pre && patch === 0 ? `${major}.${minor}.0` : `${major}.${minor + 1}.0`;
  if (kind === "major") return pre && minor === 0 && patch === 0 ? `${major}.0.0` : `${major + 1}.0.0`;
  if (!pre) return `${major}.${minor + 1}.0-${kind}.0`;
  if (kind === pre) return `${major}.${minor}.${patch}-${kind}.${preNumber + 1}`;
  if (kind === "beta") return `${major}.${minor}.${patch}-beta.0`;
  fail(`Can't go back from ${current} to alpha.`);
}

const [kind, ...words] = process.argv.slice(2);
const message = words.join(" ").trim();
if (!KINDS.includes(kind) || !message) fail('Usage: bun run release:<kind> "message"');

const branch = git("branch", "--show-current");
if (branch !== "main") fail(`Releases run only on main. You are on ${branch || "a detached HEAD"}.`);
const changes = git("status", "--porcelain");
if (changes) fail(`Commit or remove these changes first:\n${changes}`);

const pkg = JSON.parse(fs.readFileSync("package.json", "utf8"));
const version = nextVersion(pkg.version, kind);
pkg.version = version;
fs.writeFileSync("package.json", `${JSON.stringify(pkg, null, 2)}\n`);

git("add", "package.json");
git("commit", "-m", message);
git("tag", "-a", `v${version}`, "-m", message);
git("push", "--follow-tags", "origin", "main");
console.log(`Released v${version}. The publish workflow puts it on npm.`);
