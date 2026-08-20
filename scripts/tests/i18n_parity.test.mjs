import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const flatten = (value, prefix = "") =>
  Object.entries(value).flatMap(([key, child]) => {
    const path = prefix ? `${prefix}.${key}` : key;
    return child && typeof child === "object" ? flatten(child, path) : [path];
  });

test("Korean and English message keys are identical", async () => {
  const ko = JSON.parse(await readFile("frontend/messages/ko.json", "utf8"));
  const en = JSON.parse(await readFile("frontend/messages/en.json", "utf8"));

  assert.deepEqual(flatten(en).sort(), flatten(ko).sort());
});
