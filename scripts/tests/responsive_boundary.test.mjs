import assert from "node:assert/strict";
import { execFileSync, spawnSync } from "node:child_process";
import { mkdir, rm, writeFile } from "node:fs/promises";
import test from "node:test";

test("page components contain no viewport branching", () => {
  const output = execFileSync("node", ["scripts/check_page_responsive_boundary.mjs"], {
    encoding: "utf8",
  });

  assert.match(output, /0 responsive violations/);
});

test("responsive scanner reports the exact offending page line", async () => {
  const directory = "frontend/app/__responsive_probe__";
  const file = `${directory}/page.tsx`;

  try {
    await mkdir(directory, { recursive: true });
    await writeFile(file, "export const isMobile = true;\n", "utf8");
    const result = spawnSync("node", ["scripts/check_page_responsive_boundary.mjs"], {
      encoding: "utf8",
    });

    assert.equal(result.status, 1);
    assert.match(result.stderr, /frontend[\\/]app[\\/]__responsive_probe__[\\/]page\.tsx:1/);
  } finally {
    await rm(directory, { recursive: true, force: true });
  }
});
