import { test, expect } from "@playwright/test";

test.describe("Authentication Flow", () => {
  test("should allow user to register", async ({ page }) => {
    await page.goto("/register");
    const timestamp = Date.now();
    const email = `test-${timestamp}@example.com`;

    await page.fill('input[name="email"]', email);
    await page.fill('input[name="password"]', "Test123456");
    await page.fill('input[name="name"]', "Test User");
    await page.click('button[type="submit"]');

    await page.waitForURL("/");
    await expect(page).toHaveURL("/");
    await expect(page.locator("h1")).toContainText("Dashboard");
  });

  test("should allow user to login", async ({ page }) => {
    // First register a user
    const timestamp = Date.now();
    const email = `login-test-${timestamp}@example.com`;
    
    await page.goto("/register");
    await page.fill('input[name="email"]', email);
    await page.fill('input[name="password"]', "Test123456");
    await page.fill('input[name="name"]', "Test User");
    await page.click('button[type="submit"]');
    await page.waitForURL("/");

    // Logout
    await page.click('button:has-text("Account")');
    await page.click('text=Log out');
    await page.waitForURL("/login");

    // Login
    await page.fill('input[type="email"]', email);
    await page.fill('input[type="password"]', "Test123456");
    await page.click('button[type="submit"]');

    await page.waitForURL("/");
    await expect(page).toHaveURL("/");
  });

  test("should redirect to login if not authenticated", async ({ page }) => {
    await page.goto("/transactions");
    await page.waitForURL("/login");
    await expect(page).toHaveURL("/login");
  });
});
