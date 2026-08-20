import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { existsSync } from "node:fs";
import { join, relative, resolve, sep } from "node:path";

const backendRoot = resolve("backend");
const backendVolume = backendRoot.replaceAll("\\", "/");
const files = process.argv
  .slice(2)
  .map((file) => resolve(file))
  .filter((file) => file === backendRoot || file.startsWith(`${backendRoot}${sep}`))
  .map((file) => relative(backendRoot, file).replaceAll("\\", "/"));

function dockerAvailable() {
  return spawnSync("docker", ["info"], { stdio: "ignore" }).status === 0;
}

function dockerRuff(args) {
  const image = spawnSync("docker", ["compose", "images", "-q", "backend"], {
    encoding: "utf8",
  });
  assert.equal(image.status, 0, "backend image lookup failed");
  assert.notEqual(image.stdout.trim(), "", "backend image must be built before committing Python");

  const result = spawnSync(
    "docker",
    [
      "run",
      "--rm",
      "--volume",
      `${backendVolume}:/app`,
      "--workdir",
      "/app",
      image.stdout.trim(),
      "ruff",
      ...args,
      ...files,
    ],
    { encoding: "utf8", stdio: "inherit" },
  );
  assert.equal(result.status, 0, `ruff ${args.join(" ")} failed`);
}

function venvRuff(args) {
  const ruffBin = join(backendRoot, ".venv", "bin", "ruff");
  assert.ok(
    existsSync(ruffBin),
    "Docker is unavailable and backend/.venv/bin/ruff is missing. " +
      "Create it with: cd backend && uv venv --python 3.12 && uv pip install -e '.[dev]'",
  );
  const result = spawnSync(ruffBin, [...args, ...files], {
    cwd: backendRoot,
    encoding: "utf8",
    stdio: "inherit",
  });
  assert.equal(result.status, 0, `ruff ${args.join(" ")} failed`);
}

if (files.length > 0) {
  const runRuff = dockerAvailable() ? dockerRuff : venvRuff;
  runRuff(["check", "--fix"]);
  runRuff(["format"]);
}
