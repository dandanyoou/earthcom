import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import test from "node:test";

function dockerAvailable() {
  return spawnSync("docker", ["info"], { stdio: "ignore" }).status === 0;
}

function composeConfig() {
  return spawnSync("docker", ["compose", "config", "--format", "json"], {
    encoding: "utf8",
  });
}

test("compose starts the three stateful dependencies with health checks", (t) => {
  if (!dockerAvailable()) {
    // Native macOS runs use Homebrew services instead; CI keeps this contract.
    t.skip("docker is unavailable on this machine");
    return;
  }
  const result = composeConfig();
  assert.equal(result.status, 0, result.stderr);
  const config = JSON.parse(result.stdout);

  for (const service of ["postgres", "redis", "minio"]) {
    assert.ok(config.services[service], `${service} service is missing`);
    assert.ok(config.services[service].healthcheck, `${service} healthcheck is missing`);
  }

  assert.equal(config.services.postgres.image, "pgvector/pgvector:pg16");
  assert.equal(config.services.redis.image, "redis:7-alpine");
});
