import { expect, test as setup } from "@playwright/test";
import fs from "node:fs";
import path from "node:path";

const BACKEND = "http://localhost:8000";
export const STORAGE_STATE = path.join(process.cwd(), "../test-results/frontend/auth-state.json");

/** One API login for the whole suite — the UI login flow keeps its own test,
    and everything else reuses this token, staying clear of the login rate limit. */
setup("authenticate", async ({ request }) => {
  const health = await request.get(`${BACKEND}/health/ready`).catch(() => null);
  if (!health?.ok()) {
    throw new Error(
      "backend is not running — start it with `cd backend && .venv/bin/python -m app.server` " +
        "and seed it with `.venv/bin/python -m scripts.seed_demo`",
    );
  }
  const response = await request.post(`${BACKEND}/api/v1/auth/login`, {
    data: { email: "minseok@pangaea.dev", password: "pangaea-demo1!" },
  });
  expect(response.ok()).toBeTruthy();
  const body = await response.json();
  fs.mkdirSync(path.dirname(STORAGE_STATE), { recursive: true });
  fs.writeFileSync(
    STORAGE_STATE,
    JSON.stringify({
      cookies: [],
      origins: [
        {
          origin: "http://localhost:3000",
          localStorage: [{ name: "pangaea_access", value: body.data.access_token }],
        },
      ],
    }),
  );
});
