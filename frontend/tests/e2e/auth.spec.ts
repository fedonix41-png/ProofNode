import { test, expect } from '@playwright/test';

test.describe('TMA Auth Flow', () => {
  test('should initialize mock telegram data and load the application', async ({ page }) => {
    // Navigate to root
    await page.goto('/');

    // Wait for the app to load and the bottom navigation to be visible
    await expect(page.locator('.bottom-nav')).toBeVisible();
    
    // Verify the tabs are rendered correctly
    await expect(page.locator('.bottom-nav')).toContainText('Radar');
    await expect(page.locator('.bottom-nav')).toContainText('Arena');
    await expect(page.locator('.bottom-nav')).toContainText('Cabinet');
  });
});
