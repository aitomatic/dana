import { test, expect } from '@playwright/test';
import path from 'path';

test('test', async ({ page }) => {
    await page.goto('http://localhost:4041/agents?tab=my');
    await page.getByRole('link', { name: 'Library' }).click();

    try {
        await page.getByText('alphabet-10k-2024.pdf').waitFor({ timeout: 2000 });

        // File exists, proceed with deletion
        await page.getByRole('row', { name: 'data:image/svg+xml,%3csvg%' }).getByRole('button').click();
        await page.getByRole('menuitem', { name: 'Delete' }).click();
        await page.getByRole('button', { name: 'Delete' }).click();
    } catch {
        // File doesn't exist, continue to upload
        console.log('File not found, proceeding to upload');
    }

    // Upload file from local directory
    await page.getByRole('button', { name: 'Upload File' }).click();

    // Wait for file chooser before clicking Browse Files
    const fileChooserPromise = page.waitForEvent('filechooser');
    await page.getByText('Browse Files').click();
    const fileChooser = await fileChooserPromise;
    await fileChooser.setFiles(path.join(__dirname, 'alphabet-10k-2024.pdf'));

    await page.getByRole('button', { name: 'Finish' }).click();

    // Wait for 5 seconds
    await page.waitForTimeout(5000);

    // Click Finish again
    await page.getByRole('button', { name: 'Finish' }).click();

    await page.getByRole('link', { name: 'Dana Expert Agents' }).click();

    await page.getByRole('button', { name: 'Pre-trained Agents' }).click();
    await page.waitForTimeout(1000);
    await page.getByRole('button', { name: 'Pre-trained Agents' }).click();
    await page.getByText('Lama').click();
    await page.getByRole('button', { name: 'Train from this agent' }).click();
    await page.getByRole('button', { name: 'Close toast' }).click();
    await page.getByRole('textbox').click();
    await page.getByRole('textbox').fill('be a junior financial analyst that has the most basic finance knowledge');
    await page.getByRole('button', { name: 'Send message' }).click();
    await page.waitForTimeout(10000);
    await page.locator('textarea').click();
    // await page.locator('textarea').fill('add only 1 most essential topic to domain knowledge');
    // await page.getByRole('button', { name: 'Send message' }).click();
    // await page.waitForTimeout(10000);
    // await page.getByRole('heading', { name: 'Nice! You have added a new' }).click();
    await page.locator('textarea').fill('add only 1 most essential topic to domain knowledge');
    await page.getByRole('button', { name: 'Send message' }).click();

    // Retry loop
    for (let i = 0; i < 3; i++) {
        const niceHeading = await page.getByRole('heading', { name: 'Nice! You have added a new' }).isVisible({ timeout: 30000 }).catch(() => false);

        if (niceHeading) {
            break;
        }

        // Not found, try again
        await page.locator('textarea').fill('add only 1 most essential topic to domain knowledge');
        await page.getByRole('button', { name: 'Send message' }).click();
        await page.waitForTimeout(30000);
    }

    await page.getByRole('heading', { name: 'Nice! You have added a new' }).click();
    await page.locator('.p-1').click();
    await page.locator('button').filter({ hasText: 'Resources' }).click();
    await page.getByRole('button', { name: 'Documents' }).click();
    await page.locator('div').filter({ hasText: /^Add from Library$/ }).getByRole('button').click();
    await page.getByRole('checkbox').first().check();
    await page.getByRole('button', { name: 'Add 1 File(s)' }).click();
    await page.getByRole('listitem').click();
    await page.getByRole('button', { name: 'Close toast' }).click();
    await page.getByRole('button', { name: 'Use Mode' }).click();
    await page.getByTestId('chat-input').fill('how to calculate net profit');
    await page.getByTestId('send-message-button').getByRole('img').click();
});