import { test, expect } from '@playwright/test';

test.describe('All Agents Hi Interaction Test', () => {
    const agents = ['Lama', 'Sofia', 'Nova', 'Jordan'];

    for (const agentName of agents) {
        test(`should test "Hi" interaction with ${agentName} agent`, async ({ page }) => {
            // Step 1: Navigate to the Dana Studio homepage
            await page.goto('http://127.0.0.1:8080/');

            // Wait for the page to load and verify title
            await expect(page).toHaveTitle(/Dana Agent Studio/);

            // Wait for the main content to be visible
            await expect(page.getByRole('heading', { name: 'Dana Agent Studio' })).toBeVisible();

            // Step 2: Find and click on "Pre-trained Agent" or "Dana Expert Agents" section
            const expertAgentsLink = page.getByRole('link', { name: /Dana Expert Agents|Pre-trained Agent/i });
            await expect(expertAgentsLink).toBeVisible();
            await expertAgentsLink.click();

            // Wait for the expert agents page to load
            await page.waitForLoadState('networkidle');

            // Step 3: Find and select the specific agent
            const agentElement = page.locator(`text=${agentName}`);
            await expect(agentElement).toBeVisible();
            await agentElement.click();

            // Wait for agent details to load
            await page.waitForLoadState('networkidle');

            // Step 4: Click "Save to My Agent and Use" button
            const saveAndUseButton = page.getByRole('button', { name: /Save to My Agent and Use|Save and Use/i });
            await expect(saveAndUseButton).toBeVisible();
            await saveAndUseButton.click();

            // Wait for the agent to be ready for interaction
            await page.waitForLoadState('networkidle');

            // Step 5: Test "Hi" interaction
            const chatInput = page.locator('input[type="text"], textarea, [contenteditable="true"], [data-testid*="chat-input"]').first();
            await expect(chatInput).toBeVisible();

            await chatInput.fill('Hi');
            await chatInput.press('Enter');

            // Wait for response to be generated
            await page.waitForTimeout(3000);

            // Verify that an answer is displayed
            const chatMessages = page.locator('.message, .chat-message, [data-testid*="message"], .response, .answer').last();
            await expect(chatMessages).toBeVisible();

            // Log the response for debugging
            const responseText = await chatMessages.textContent();
            console.log(`${agentName} agent response to "Hi":`, responseText);
        });
    }

});
