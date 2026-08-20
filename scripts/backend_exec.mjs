#!/usr/bin/env node
// Runs a backend command inside docker compose when Docker is available,
// otherwise falls back to the native virtualenv at backend/.venv (macOS without Docker).
import { spawnSync } from "node:child_process";
import { existsSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const backendDir = path.join(repoRoot, "backend");
const args = process.argv.slice(2);

if (args.length === 0) {
  console.error("usage: backend_exec.mjs <command> [args...]");
  process.exit(2);
}

function dockerAvailable() {
  const probe = spawnSync("docker", ["info"], { stdio: "ignore" });
  return probe.status === 0;
}

let result;
if (dockerAvailable()) {
  result = spawnSync("docker", ["compose", "run", "--rm", "backend", ...args], {
    cwd: repoRoot,
    stdio: "inherit",
  });
} else {
  const venvBin = path.join(backendDir, ".venv", "bin");
  if (!existsSync(venvBin)) {
    console.error(
      "Docker is unavailable and backend/.venv is missing. " +
        "Create it with: cd backend && uv venv --python 3.12 && uv pip install -e '.[dev]'",
    );
    process.exit(1);
  }
  const [command, ...rest] = args;
  const localCommand = existsSync(path.join(venvBin, command))
    ? path.join(venvBin, command)
    : command;
  result = spawnSync(localCommand, rest, {
    cwd: backendDir,
    stdio: "inherit",
    env: { ...process.env, PATH: `${venvBin}:${process.env.PATH ?? ""}` },
  });
}

process.exit(result.status ?? 1);
