import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { mkdtemp, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";

function run(args) {
  if (process.platform === "win32") {
    const quote = (part) => (/[\s"&|<>^]/.test(part) ? `"${part.replaceAll('"', '""')}"` : part);
    const command = ["pnpm", ...args].map(quote).join(" ");
    return spawnSync(process.env.ComSpec ?? "cmd.exe", ["/d", "/s", "/c", command], {
      encoding: "utf8",
    });
  }

  return spawnSync("pnpm", args, { encoding: "utf8" });
}

test("formatter rejects unformatted markdown and accepts its own output", async () => {
  const directory = await mkdtemp(join(tmpdir(), "pangaea-format-"));
  const file = join(directory, "probe.md");

  try {
    await writeFile(file, "# heading\n\n-   badly spaced\n", "utf8");

    const before = run(["exec", "prettier", "--check", file]);
    assert.notEqual(before.status, 0, "unformatted Markdown must be rejected");

    const format = run(["exec", "prettier", "--write", file]);
    assert.equal(format.status, 0, `${format.stdout}\n${format.stderr}`);

    const after = run(["exec", "prettier", "--check", file]);
    assert.equal(after.status, 0, `${after.stdout}\n${after.stderr}`);
  } finally {
    await rm(directory, { recursive: true, force: true });
  }
});

test("linter rejects an explicit-any API-key literal", async () => {
  const file = ".toolchain-probe.ts";

  try {
    await writeFile(file, 'const secret: any = "sk-probe";\n', "utf8");
    const result = run(["exec", "eslint", file, "--max-warnings=0"]);

    assert.notEqual(result.status, 0, "unsafe frontend source must be rejected");
    assert.match(`${result.stdout}\n${result.stderr}`, /API 키|no-explicit-any/);
  } finally {
    await rm(file, { force: true });
  }
});

test("linter rejects Korean copy embedded in JSX", async () => {
  const file = ".toolchain-copy-probe.tsx";

  try {
    await writeFile(file, "export const Probe = () => <p>하드코딩</p>;\n", "utf8");
    const result = run(["exec", "eslint", file, "--max-warnings=0"]);

    assert.notEqual(result.status, 0, "hardcoded Korean JSX copy must be rejected");
    assert.match(`${result.stdout}\n${result.stderr}`, /messages/);
  } finally {
    await rm(file, { force: true });
  }
});
