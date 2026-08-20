import { defineConfig } from "@playwright/test";
import path from "node:path";

const storageState = path.join(__dirname, "../test-results/frontend/auth-state.json");

export default defineConfig({
  testDir: "./e2e",
  outputDir: "../test-results/frontend",
  snapshotDir: "./e2e/__snapshots__",
  fullyParallel: true,
  forbidOnly: true,
  retries: 0,
  reporter: "line",
  use: {
    baseURL: "http://localhost:3000",
    browserName: "chromium",
    colorScheme: "light",
    locale: "ko-KR",
    screenshot: "only-on-failure",
    trace: "retain-on-failure",
  },
  projects: [
    { name: "setup", testMatch: /auth\.setup\.ts/ },
    {
      name: "chromium",
      dependencies: ["setup"],
      testIgnore: /auth\.setup\.ts/,
      use: { storageState },
    },
  ],
  webServer: {
    command: "pnpm build && pnpm start",
    url: "http://localhost:3000",
    reuseExistingServer: false,
    timeout: 120_000,
  },
});
