import { readFile } from "node:fs/promises";

const flatten = (value, prefix = "") =>
  Object.entries(value).flatMap(([key, child]) => {
    const path = prefix ? `${prefix}.${key}` : key;
    return child && typeof child === "object" ? flatten(child, path) : [path];
  });

const [ko, en] = await Promise.all([
  readFile("frontend/messages/ko.json", "utf8").then(JSON.parse),
  readFile("frontend/messages/en.json", "utf8").then(JSON.parse),
]);

const koKeys = new Set(flatten(ko));
const enKeys = new Set(flatten(en));
const missingFromKorean = [...enKeys].filter((key) => !koKeys.has(key)).sort();
const missingFromEnglish = [...koKeys].filter((key) => !enKeys.has(key)).sort();

if (missingFromKorean.length || missingFromEnglish.length) {
  if (missingFromKorean.length) {
    console.error(`Missing from Korean: ${missingFromKorean.join(", ")}`);
  }
  if (missingFromEnglish.length) {
    console.error(`Missing from English: ${missingFromEnglish.join(", ")}`);
  }
  process.exitCode = 1;
} else {
  console.log(`i18n parity passed (${koKeys.size} leaf keys)`);
}
