import { test, expect } from '@playwright/test';

test.describe('All Agents Hi Test', () => {
    const agents = ['Lama', 'Sofia', 'Nova', 'Jordan'];

    for (let i = 0; i < agents.length; i++) {
        const agentName = agents[i];

        test(`should test "hi" interaction with ${agentName} agent`, async ({ page }) => {
            // Navigate to agents explore page
            await page.goto('http://localhost:4041/agents?tab=explore');
            await page.getByText(agentName).click();
            await page.getByRole('button', { name: 'Train from this agent' }).click();

            // Switch to use mode and test
            await page.getByRole('button', { name: 'Use Mode' }).click();
            await page.getByTestId('chat-input').click();
            await page.getByTestId('chat-input').fill('hi');
            await page.getByTestId('send-message-button').getByRole('img').click();
        });
    }
});