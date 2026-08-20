import { readdir, readFile } from "node:fs/promises";
import { relative, resolve } from "node:path";

const roots = [
  { directory: "frontend/app", pageFilesOnly: true },
  { directory: "frontend/components/feature", pageFilesOnly: false },
];

const forbiddenPatterns = [
  ["matchMedia", /\bmatchMedia\b/],
  ["innerWidth", /\binnerWidth\b/],
  ["useMediaQuery", /\buseMediaQuery\b/],
  ["isMobile", /\bisMobile\b/],
  ["isDesktop", /\bisDesktop\b/],
  ["responsive utility prefix", /\b(?:sm|md|lg|xl|2xl):[a-z]/i],
];

async function collectFiles(directory, pageFilesOnly) {
  let entries;
  try {
    entries = await readdir(directory, { withFileTypes: true });
  } catch (error) {
    if (error && typeof error === "object" && "code" in error && error.code === "ENOENT") {
      return [];
    }
    throw error;
  }

  const nested = await Promise.all(
    entries.map(async (entry) => {
      const path = resolve(directory, entry.name);
      if (entry.isDirectory()) return collectFiles(path, pageFilesOnly);
      if (!entry.isFile() || !entry.name.endsWith(".tsx")) return [];
      if (pageFilesOnly && !/^(?:page|layout)\.tsx$/.test(entry.name)) return [];
      return [path];
    }),
  );

  return nested.flat();
}

const files = (
  await Promise.all(
    roots.map(({ directory, pageFilesOnly }) => collectFiles(directory, pageFilesOnly)),
  )
).flat();
const violations = [];

for (const file of files) {
  const lines = (await readFile(file, "utf8")).split(/\r?\n/);
  lines.forEach((line, index) => {
    forbiddenPatterns.forEach(([label, pattern]) => {
      if (pattern.test(line)) {
        violations.push(`${relative(process.cwd(), file)}:${index + 1}: ${label}`);
      }
    });
  });
}

violations.forEach((violation) => console.error(violation));
console.log(`${violations.length} responsive violations`);

if (violations.length) process.exitCode = 1;
