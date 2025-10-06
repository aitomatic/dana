import { test, expect } from '@playwright/test';

test('test', async ({ page }) => {
    await page.goto('http://localhost:4041/agents?tab=explore');
    await page.getByText('Lama').click();
    await page.getByRole('button', { name: 'Train from this agent' }).click();

    // First interaction - set basic prompt
    await page.getByRole('textbox', { name: 'Type your message' }).click();
    await page.getByRole('textbox', { name: 'Type your message' }).fill('be a junior financial analyst that has the most basic knowledge');
    await page.getByRole('button', { name: 'Send message' }).click();

    // Second interaction - add refinements
    await page.getByRole('textbox', { name: 'Type your message' }).click();
    await page.getByRole('textbox', { name: 'Type your message' }).fill('add only the most basic');
    await page.getByRole('button', { name: 'Send message' }).click();

    // Click through all available option buttons
    while (await page.getByRole('button').filter({ hasText: /^\d+\./ }).first().isVisible({ timeout: 2000 }).catch(() => false)) {
        await page.getByRole('button').filter({ hasText: /^\d+\./ }).first().click();
        await page.waitForTimeout(500); // Small delay to let UI update
    }

    // Navigate to resources
    await page.locator('button').filter({ hasText: 'Resources' }).click();
    await page.getByRole('button', { name: 'Documents' }).click();
    await page.getByRole('button', { name: 'Add from Library' }).click();

    // Select first checkbox and add
    await page.getByRole('checkbox').first().click();
    await page.getByRole('button', { name: /Add.*File/i }).click();
    await page.getByRole('button', { name: 'Close toast' }).click();

    // Switch to use mode and test
    await page.getByRole('button', { name: 'Use Mode' }).click();
    await page.getByTestId('chat-input').click();
    await page.getByTestId('chat-input').fill('hi');
    await page.getByTestId('send-message-button').getByRole('img').click();

    await page.goto('http://localhost:4041/agents/67/chat/11');
    await page.getByTestId('chat-input').fill('what is google total revenue in 2024');
    await page.getByTestId('chat-input').click();
    await page.getByTestId('chat-input').fill('what is the gross margin');
});
