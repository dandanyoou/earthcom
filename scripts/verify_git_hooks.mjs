import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { mkdtemp, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";

function run(command, args, options = {}) {
  return spawnSync(command, args, {
    encoding: "utf8",
    ...options,
  });
}

function output(result) {
  return `${result.stdout ?? ""}\n${result.stderr ?? ""}`.trim();
}

const probe = ".hook-probe.ts";
const temporaryDirectory = await mkdtemp(join(tmpdir(), "pangaea-hooks-"));
const invalidMessage = join(temporaryDirectory, "COMMIT_EDITMSG");

try {
  await writeFile(probe, 'const secret: any = "sk-hook-probe";\n', "utf8");
  assert.equal(run("git", ["add", "--", probe]).status, 0, "failed to stage pre-commit probe");

  const preCommit = run("git", ["hook", "run", "pre-commit"]);
  assert.notEqual(preCommit.status, 0, "pre-commit accepted unsafe staged TypeScript");
  assert.match(output(preCommit), /API 키|no-explicit-any/);

  assert.equal(run("git", ["reset", "--quiet", "HEAD", "--", probe]).status, 0);
  await rm(probe, { force: true });

  await writeFile(invalidMessage, "not conventional\n", "utf8");
  const commitMessage = run("git", ["hook", "run", "commit-msg", "--", invalidMessage]);
  assert.notEqual(commitMessage.status, 0, "commit-msg accepted a non-conventional message");
  assert.match(output(commitMessage), /type-empty|subject-empty/);

  const prePush = run("git", ["hook", "run", "pre-push"]);
  assert.equal(prePush.status, 0, output(prePush));

  console.log("pre-commit rejected unsafe source");
  console.log("commit-msg rejected a non-conventional message");
  console.log("pre-push completed the repository verification gate");
} finally {
  run("git", ["reset", "--quiet", "HEAD", "--", probe]);
  await rm(probe, { force: true });
  await rm(temporaryDirectory, { recursive: true, force: true });
}
