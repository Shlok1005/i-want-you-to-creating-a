#!/usr/bin/env node
/**
 * Cross-platform npm start helper.
 * Finds a working Python 3 binary on Windows/macOS/Linux, then runs server.py.
 */
const { spawnSync } = require("child_process");
const path = require("path");

const root = __dirname;
const server = path.join(root, "server.py");
const checkOnly = process.argv.includes("--check");

const candidates = [
  ["py", "-3"],
  ["py"],
  ["python"],
  ["python3"],
];

function pythonWorks(cmd) {
  const result = spawnSync(cmd[0], [...cmd.slice(1), "-c", "import sys; print(sys.version_info[0])"], {
    encoding: "utf8",
  });
  if (result.error || result.status !== 0) return false;
  return String(result.stdout || "").trim().startsWith("3");
}

function printInstallHelp() {
  console.error("");
  console.error("Python 3 was not found.");
  console.error("");
  console.error("On Windows PowerShell, try one of these:");
  console.error("  py server.py");
  console.error("  python server.py");
  console.error("  .\\start.bat");
  console.error("");
  console.error("If those fail:");
  console.error("  1. Install Python from https://www.python.org/downloads/");
  console.error('  2. Check "Add python.exe to PATH" during setup');
  console.error("  3. Open a NEW PowerShell window");
  console.error("");
  console.error("If Windows opens the Microsoft Store instead, disable App execution aliases:");
  console.error("  Settings > Apps > Advanced app settings > App execution aliases");
  console.error("  Turn OFF python.exe and python3.exe");
  console.error("");
}

const python = candidates.find(pythonWorks);
if (!python) {
  printInstallHelp();
  process.exit(1);
}

const args = checkOnly
  ? [...python.slice(1), "-m", "py_compile", server]
  : [...python.slice(1), server, ...process.argv.slice(2).filter((a) => a !== "--check")];

const result = spawnSync(python[0], args, {
  cwd: root,
  stdio: "inherit",
  shell: false,
});

if (result.error) {
  console.error(result.error.message);
  printInstallHelp();
  process.exit(1);
}

process.exit(result.status == null ? 1 : result.status);
