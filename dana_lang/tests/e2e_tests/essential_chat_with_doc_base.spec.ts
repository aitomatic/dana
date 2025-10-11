import { test, expect } from '@playwright/test';

test('test', async ({ page }) => {
    await page.goto('http://127.0.0.1:8080/agents?tab=explore');
    await page.getByRole('img', { name: 'Lama avatar' }).click();
    await page.getByRole('button', { name: 'Train from this agent' }).click();
    await page.locator('button').filter({ hasText: 'Resources' }).click();
    await page.getByRole('button', { name: 'Documents' }).click();
    await page.getByRole('button', { name: 'Add from Library' }).click();
    await page.getByRole('checkbox').click();
    await page.getByRole('button', { name: 'Add 1 File(s)' }).click();
    await page.getByRole('listitem').click();
    await page.getByRole('button', { name: 'Close toast' }).click();
    await page.getByRole('button', { name: 'Use Mode' }).click();
    await page.getByTestId('chat-input').click();
    await page.getByTestId('chat-input').fill('hi');
    await page.goto('http://127.0.0.1:8080/agents/8/chat/4');
    await page.getByTestId('chat-input').fill('what is annual revenue of google in 2024');
});