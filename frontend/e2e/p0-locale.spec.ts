import { expect, test } from "@playwright/test";

test.use({ viewport: { width: 720, height: 900 } });

test("locale switch preserves the current path and preference", async ({ context, page }) => {
  await page.goto("/ko/demo");
  await expect(page.locator("html")).toHaveAttribute("lang", "ko");

  const switcher = page.getByTestId("locale-switcher");
  await switcher.getByRole("button", { name: "English" }).click();

  await expect(page).toHaveURL(/\/en\/demo$/);
  await expect(page.locator("html")).toHaveAttribute("lang", "en");
  await expect(page.locator("body")).toHaveCSS("word-break", "normal");
  await expect(page.locator("body")).toHaveCSS("overflow-wrap", "break-word");
  await expect(switcher.getByRole("button", { name: "English" })).toHaveAttribute(
    "aria-pressed",
    "true",
  );

  const localeCookie = (await context.cookies()).find((cookie) => cookie.name === "NEXT_LOCALE");
  expect(localeCookie?.value).toBe("en");

  await page.reload();
  await expect(page).toHaveURL(/\/en\/demo$/);
  await expect(page.locator("html")).toHaveAttribute("lang", "en");
});

test("root is canonicalized and unsupported locales return 404", async ({ page }) => {
  await page.goto("/");
  await expect(page).toHaveURL(/\/ko(\/home)?$/);

  const response = await page.request.get("/fr/demo", { maxRedirects: 0 });
  expect(response.status()).toBe(404);
});
