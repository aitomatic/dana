import { test, expect } from '@playwright/test';
import { time } from 'console';

import { defineConfig } from '@playwright/test';

export default defineConfig({
    timeout: 99999999, // Set a very large default timeout
});

test('test', async ({ page }) => {
    await page.goto('http://127.0.0.1:8080/agents?tab=explore');
    await page.getByText('General PurposeLamaChat with').click();
    await page.getByRole('button', { name: 'Train from this agent' }).click();
    await page.getByRole('textbox', { name: 'Type your message' }).click();
    await page.getByRole('textbox', { name: 'Type your message' }).fill('be a junior financial analyst');
    await page.getByRole('textbox', { name: 'Type your message' }).click();
    await page.getByRole('textbox', { name: 'Type your message' }).fill('financial statement analysis');
    await page.getByTestId('rf__wrapper').locator('div').filter({ hasText: 'LamaAI' }).nth(1).click();
    await page.getByTestId('rf__wrapper').locator('div').filter({ hasText: 'LamaAI' }).nth(1).click();
    await page.getByTestId('rf__wrapper').locator('div').filter({ hasText: 'LamaAI' }).nth(1).click();
    await page.locator('button').filter({ hasText: 'Resources' }).click();
    await page.getByTestId('rf__node-General Purpose').click();
    await page.getByRole('textbox', { name: 'Type your message' }).click();
    await page.getByRole('textbox', { name: 'Type your message' }).fill('add only income statement analysis');
    await page.getByTestId('rf__node-General Purpose').click();
    await page.getByRole('button', { name: '1. Generate comprehensive' }).nth(1).click();
    await page.getByRole('button', { name: 'Use Mode' }).click();
    await page.getByTestId('chat-input').click();
    await page.getByTestId('chat-input').fill('hi');
    await page.goto('http://127.0.0.1:8080/agents/11/chat/5');
    await page.getByTestId('chat-input').fill('what is google annual revenue in 2024');
    await page.getByRole('button', { name: 'Train mode' }).click();
    await page.getByRole('button', { name: 'Documents' }).click();
    await page.getByRole('button', { name: 'Add from Library' }).click();
    await page.getByRole('checkbox').click();
    await page.getByRole('button', { name: 'Add 1 File(s)' }).click();
    await page.getByRole('region', { name: 'Notifications alt+T' }).getByRole('listitem').click();
    await page.getByRole('button', { name: 'Use Mode' }).click();
    await page.getByTestId('chat-input').fill('hi');
    await page.goto('http://127.0.0.1:8080/agents/11/chat/6');
    await page.getByTestId('chat-input').fill('analyze income and profit');
    await page.getByText('If you need the precise').click();
    await page.getByText('If you need the precise').click();
    await page.getByTestId('chat-input').click();
    await page.getByTestId('chat-input').fill('give precise revenue, net income, profit margin and analyze');
});