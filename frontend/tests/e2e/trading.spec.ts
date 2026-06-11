import { test, expect } from '@playwright/test';

test.describe('Trading & Cabinet Flows', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('navigate Leaderboard (Arena)', async ({ page }) => {
    await page.click('text=Arena');
    await expect(page.getByText('The Arena')).toBeVisible();
  });

  test('Cabinet: 1-Click Copy Trading Setup', async ({ page }) => {
    await page.click('text=Cabinet');
    await expect(page.getByText('1-Click Copy Trading')).toBeVisible();

    const pkInput = page.getByPlaceholder('Paste 64-char Hex Private Key');
    await pkInput.fill('0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef');
    
    await page.click('text=Set up 1-Click Copying');
    
    // It should process and show Setup Complete
    await expect(page.getByText('Setup Complete')).toBeVisible();
  });

  test('Cabinet: Signal Creation', async ({ page }) => {
    await page.route('/api/traders/*/signals', async route => {
      await route.fulfill({
        status: 200,
        json: { id: 999, token_address: 'EQ123456789', blockchain: 'TON', direction: 'BUY' }
      });
    });

    await page.click('text=Cabinet');
    await expect(page.getByText('Broadcast Signal')).toBeVisible();

    await page.getByPlaceholder('Token Address').fill('EQ123456789');
    await page.click('text=BUY', { exact: true }); 
    
    // Mock the alert to automatically dismiss it so the test can proceed
    page.on('dialog', dialog => dialog.accept());
    
    await page.click('text=Publish Signal');
    
    // Open signal should appear with a Close button
    await expect(page.getByText('Close').first()).toBeVisible();
  });

  test('Premium Upsell Flow', async ({ page }) => {
    await page.click('text=Cabinet');
    // Ensure the PremiumUpsell component renders. Assuming it has text 'Pro' or 'Premium' or 'Unlock'
    // We will verify something that is typically in the Premium upsell component.
    await expect(page.locator('text=Premium').first()).toBeVisible();
  });
});
