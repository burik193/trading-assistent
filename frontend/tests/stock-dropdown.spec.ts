import { test, expect } from "@playwright/test";

test.describe("Stock dropdown", () => {
  test("opens and shows stocks from API", async ({ page }) => {
    await page.goto("/");

    const trigger = page.getByTestId("stock-dropdown-trigger");
    await expect(trigger).toBeVisible();
    await expect(trigger).toHaveText(/Select a stock\.\.\./);

    await trigger.click();

    await page.getByPlaceholder("Search stocks...").waitFor({ state: "visible" });

    const list = page.getByTestId("stock-list");
    await list.waitFor({ state: "visible", timeout: 10000 });

    const options = list.locator("li");
    const count = await options.count();
    expect(count).toBeGreaterThan(0);

    const firstText = await options.first().textContent();
    expect(firstText?.trim().length).toBeGreaterThan(0);
  });

  test("search filters stocks", async ({ page }) => {
    await page.goto("/");

    await page.getByTestId("stock-dropdown-trigger").click();
    await page.getByTestId("stock-list").waitFor({ state: "visible", timeout: 10000 });

    const search = page.getByPlaceholder("Search stocks...");
    await search.fill("Apple");

    const list = page.getByTestId("stock-list");
    const options = list.locator("li");
    await expect(options.first()).toBeVisible({ timeout: 3000 });
    const firstText = await options.first().textContent();
    expect(firstText?.toLowerCase()).toContain("apple");
  });
});
