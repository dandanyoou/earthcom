import { expect, test, type Page } from "@playwright/test";

/**
 * Full-stack smoke over the seeded demo slice.
 * Requires the backend on :8000 with `python -m scripts.seed_demo` applied.
 */

const EMAIL = "minseok@pangaea.dev";
const PASSWORD = "pangaea-demo1!";

async function loginThroughUi(page: Page) {
  await page.goto("/ko/login");
  await page.getByRole("textbox", { name: "이메일" }).fill(EMAIL);
  await page.getByRole("textbox", { name: "비밀번호" }).fill(PASSWORD);
  await page.getByRole("button", { name: "로그인" }).click();
  await page.waitForURL(/\/ko\/home$/);
}

// The one test that exercises the login screen itself; every other test
// reuses the storage-state token from auth.setup.ts.
test("home renders trust temperature, city strip, and the seeded feed", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await loginThroughUi(page);

  await expect(page.locator(".temp__value")).toContainText("°");
  await expect(page.locator(".city").first()).toContainText("서울");
  await expect(page.getByText("아이 열이 39도예요")).toBeVisible();
  await expect(page.getByTestId("tab-bar")).toBeVisible();
  await expect(page.getByTestId("side-nav")).toBeHidden();
});

test("desktop promotes the tab bar into the side navigation", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto("/ko/home");
  await page.getByText("오늘은 누구를 찾고 있나요?").waitFor();

  await expect(page.getByTestId("side-nav")).toBeVisible();
  await expect(page.getByTestId("tab-bar")).toBeHidden();
});

test("write shows the parse preview with dashed estimate tags", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/ko/write");

  await page
    .locator("textarea.ta")
    .fill("리액트 대시보드 같이 손볼 분 찾아요. 2주 정도 생각하고 있어요.");
  await expect(page.getByText("이렇게 이해했어요")).toBeVisible();
  await expect(page.locator(".tag--guess").first()).toBeVisible();
});

test("crew chat shows translations, culture help, and the pre-send check", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/ko/chat");
  await page.getByText("EVA 팬게임 크루").first().click();

  await expect(page.getByText("원문 — Dieses State-Layer-Design skaliert nicht.")).toBeVisible();
  await expect(page.getByText("이렇게 읽으시면 좋아요")).toBeVisible();
  await expect(page.getByText("번역 확인 필요").first()).toBeVisible();

  await page.locator('input[aria-label="메시지를 입력하세요"]').fill("그 부분 ㅇㅋ 하시면 될 듯요");
  await expect(page.getByText("보내기 전에 한 번만 확인해 주세요")).toBeVisible();
  await expect(page.getByRole("button", { name: "그대로 보내기" })).toBeVisible();
});

test("direct search expands synonyms and finds the shader developer", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/ko/find");

  await page.locator(".findbar--input input").fill("유니티 셰이더 잘하는 사람");
  await expect(page.getByText("L. Weber")).toBeVisible();
});

test("wrap-up shows deliverable fingerprints and member temperatures", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/ko/done");

  await expect(page.getByText("함께 만든 것")).toBeVisible();
  await expect(page.getByText("기획서 v1.3.pdf")).toBeVisible();
  await expect(page.locator(".file__hash").first()).toBeVisible();
  await expect(page.getByText("L. Weber · 클라이언트 개발")).toBeVisible();
});
