import { expect, test } from "@playwright/test";
import path from "node:path";

const snapshotStyle = path.join(process.cwd(), "e2e/snapshot.css");

for (const width of [360, 414]) {
  test(`shared components preserve layout contracts at ${width}px`, async ({ page }) => {
    await page.setViewportSize({ width, height: 900 });
    await page.goto("/ko/dev/components");

    const buttons = page.getByTestId("component-button-pair").getByRole("button");
    const heights = await buttons.evaluateAll((nodes) =>
      nodes.map((node) => node.getBoundingClientRect().height),
    );
    expect(heights[0]).toBe(heights[1]);

    const overflow = await page
      .locator('[data-testid^="component-"]')
      .evaluateAll((nodes) =>
        nodes
          .filter((node) => node.scrollWidth > node.clientWidth)
          .map((node) => node.getAttribute("data-testid")),
      );
    expect(overflow).toEqual([]);

    const details = page.getByTestId("component-fold").locator("details");
    await expect(details).not.toHaveAttribute("open", "");
    await details.locator("summary").click();
    await expect(details).toHaveAttribute("open", "");

    await expect(page.locator("img")).toHaveCount(0);
    await expect(page.locator("body")).not.toContainText(/[😀-🙏🌀-🫿]/u);

    await expect(page.getByTestId("component-catalog")).toHaveScreenshot(
      `p0-components-${width}.png`,
      { animations: "disabled", maxDiffPixels: 80, stylePath: snapshotStyle },
    );
  });
}
