import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";

function docker(args) {
  const result = spawnSync("docker", args, { encoding: "utf8" });
  assert.equal(result.status, 0, `${result.stdout}\n${result.stderr}`);
  return result.stdout.trim();
}

docker(["compose", "up", "-d", "--wait", "postgres", "redis", "minio"]);

docker([
  "compose",
  "exec",
  "-T",
  "postgres",
  "psql",
  "-U",
  "pangaea",
  "-d",
  "pangaea",
  "-v",
  "ON_ERROR_STOP=1",
  "-c",
  "CREATE EXTENSION IF NOT EXISTS vector;",
]);

const vector = docker([
  "compose",
  "exec",
  "-T",
  "postgres",
  "psql",
  "-U",
  "pangaea",
  "-d",
  "pangaea",
  "-tAc",
  "SELECT extname FROM pg_extension WHERE extname = 'vector';",
]);
assert.equal(vector, "vector");

const redis = docker(["compose", "exec", "-T", "redis", "redis-cli", "ping"]);
assert.equal(redis, "PONG");

const services = docker(["compose", "ps", "--status", "running", "--services"])
  .split(/\r?\n/)
  .sort();
assert.deepEqual(services, ["minio", "postgres", "redis"]);

console.log("PostgreSQL pgvector extension is available");
console.log("Redis responded with PONG");
console.log("MinIO, PostgreSQL, and Redis are healthy");
