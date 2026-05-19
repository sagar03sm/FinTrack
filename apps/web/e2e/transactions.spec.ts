import { test, expect } from "@playwright/test";

test.describe("Transactions Flow", () => {
  test.beforeEach(async ({ page }) => {
    // Register and login before each test
    const timestamp = Date.now();
    const email = `tx-test-${timestamp}@example.com`;
    
    await page.goto("/register");
    await page.fill('input[name="email"]', email);
    await page.fill('input[name="password"]', "Test123456");
    await page.fill('input[name="name"]', "Test User");
    await page.click('button[type="submit"]');
    await page.waitForURL("/");
  });

  test("should display transactions page", async ({ page }) => {
    await page.click('a:has-text("Transactions")');
    await page.waitForURL("/transactions");
    await expect(page.locator("h1")).toContainText("Transactions");
  });

  test("should create a transaction", async ({ page }) => {
    await page.goto("/transactions");
    await page.click('button:has-text("Add Transaction")');
    
    await page.selectOption('select[name="type"]', "expense");
    await page.fill('input[type="number"]', "100");
    
    // Wait for categories to load
    await page.waitForSelector('select[name="category_id"]');
    await page.selectOption('select[name="category_id"]', { index: 0 });
    
    await page.fill('input[name="note"]', "Test expense");
    await page.fill('input[type="date"]', new Date().toISOString().split("T")[0]);
    
    await page.click('button[type="submit"]');
    
    // Wait for dialog to close
    await page.waitForSelector('button:has-text("Add Transaction")', { state: "visible" });
    
    // Verify transaction appears in table
    await expect(page.locator('table tbody tr')).toHaveCount(1);
  });

  test("should delete a transaction", async ({ page }) => {
    await page.goto("/transactions");
    await page.click('button:has-text("Add Transaction")');
    
    await page.selectOption('select[name="type"]', "expense");
    await page.fill('input[type="number"]', "50");
    await page.selectOption('select[name="category_id"]', { index: 0 });
    await page.fill('input[name="note"]', "To be deleted");
    await page.fill('input[type="date"]', new Date().toISOString().split("T")[0]);
    await page.click('button[type="submit"]');
    
    await page.waitForSelector('button:has-text("Add Transaction")', { state: "visible" });
    
    // Delete the transaction
    await page.click('button:has-text("Delete")');
    
    // Verify transaction is gone
    await expect(page.locator('table tbody tr')).toHaveCount(0);
  });
});
