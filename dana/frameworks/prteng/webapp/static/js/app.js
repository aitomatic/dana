let sessionId = null;
let isInitialized = false;
let currentPromptId = null;

// Auto-initialize when page loads
window.addEventListener('load', async () => {
    console.log('🔵 PAGE LOAD: Starting initialization...');
    await initializeSession();
    console.log('🔵 PAGE LOAD: Initialization complete, isInitialized =', isInitialized);
    // Only load prompt IDs after session is initialized
    if (isInitialized) {
        console.log('🔵 PAGE LOAD: Loading prompt IDs...');
        await loadExistingPromptIds();
    } else {
        console.log('🔴 PAGE LOAD: Session not initialized, skipping prompt ID loading');
    }
});

async function apiCall(endpoint, method = 'GET', data = null) {
    const options = {
        method: method,
        headers: {
            'Content-Type': 'application/json',
        }
    };

    if (data) {
        options.body = JSON.stringify(data);
        console.log('🔵 API REQUEST:', endpoint, 'Data:', data);
    } else {
        console.log('🔵 API REQUEST:', endpoint, 'No data');
    }

    try {
        const response = await fetch(endpoint, options);
        const result = await response.json();
        console.log('🟢 API RESPONSE:', endpoint, 'Result:', result);
        return result;
    } catch (error) {
        console.error('🔴 API ERROR:', endpoint, error);
        return { success: false, error: error.message };
    }
}

function setButtonLoading(buttonId, isLoading) {
    const button = document.getElementById(buttonId);
    if (isLoading) {
        button.disabled = true;
        button.textContent = 'Working...';
    } else {
        button.disabled = false;
        button.textContent = 'Ask AI';
    }
}

function showStatus(message, type = 'info') {
    const element = document.getElementById('status-messages');
    element.innerHTML = `<div class="status ${type}">${message}</div>`;
}

function showSection(sectionId) {
    document.getElementById(sectionId).classList.remove('hidden');
}

function showSections(...sectionIds) {
    sectionIds.forEach(id => showSection(id));
}

async function loadExistingPromptIds() {
    console.log('🔵 LOADING: Loading existing prompt IDs...');
    console.log('🔵 DEBUG: isInitialized =', isInitialized);
    try {
        const result = await apiCall('/api/prompt-ids', 'GET');
        console.log('🟢 PROMPT IDS LOADED:', result);

        if (result.success) {
            const select = document.getElementById('prompt-id-select');
            select.innerHTML = '<option value="">Select existing or create new...</option>';

            result.prompt_ids.forEach(promptId => {
                const option = document.createElement('option');
                option.value = promptId;
                option.textContent = promptId;
                select.appendChild(option);
            });

            // Add session ID as default option
            if (sessionId && !result.prompt_ids.includes(sessionId)) {
                const option = document.createElement('option');
                option.value = sessionId;
                option.textContent = `${sessionId} (default)`;
                select.appendChild(option);
            }

            console.log('🟢 SUCCESS: Prompt IDs loaded into dropdown');
        }
    } catch (error) {
        console.log('🔴 ERROR: Failed to load prompt IDs:', error);
    }
}

async function loadPromptId() {
    const selectedId = document.getElementById('prompt-id-select').value;
    console.log('🔵 USER ACTION: loadPromptId() called');
    console.log('🔵 USER INPUT: selected prompt_id =', selectedId);

    if (selectedId) {
        currentPromptId = selectedId;
        console.log('🟢 SUCCESS: Prompt ID loaded:', selectedId);
        showStatus(`✅ Loaded prompt ID: ${selectedId}`, 'success');

        // Load the system prompt for this ID
        await loadSystemPromptForId(selectedId);
    } else {
        currentPromptId = null;
        console.log('ℹ️ INFO: No prompt ID selected');
    }
}

async function createNewPromptId() {
    const inputId = document.getElementById('prompt-id-input').value.trim();
    console.log('🔵 USER ACTION: createNewPromptId() called');
    console.log('🔵 USER INPUT: new prompt_id =', inputId);

    if (!inputId) {
        console.log('🔴 ERROR: No prompt ID provided');
        showStatus('Please enter a prompt ID', 'error');
        return;
    }

    currentPromptId = inputId;
    document.getElementById('prompt-id-input').value = '';
    console.log('🟢 SUCCESS: New prompt ID created:', inputId);
    showStatus(`✅ Created new prompt ID: ${inputId}`, 'success');

    // Load the system prompt for this new ID (will be default)
    await loadSystemPromptForId(inputId);
}

async function loadSystemPromptForId(promptId) {
    console.log('🟡 LOADING: Loading system prompt for ID:', promptId);
    try {
        const result = await apiCall('/api/start', 'POST', { query: 'load system prompt', prompt_id: promptId });
        console.log('🟢 SYSTEM PROMPT LOADED FOR ID:', result);

        if (result.success) {
            document.getElementById('system-prompt').textContent = result.system_message || '(No system prompt)';

            // Update version display
            const versionDisplay = document.getElementById('prompt-version');
            if (result.version) {
                versionDisplay.textContent = `(v${result.version})`;
            } else {
                versionDisplay.textContent = '(v1)';
            }

            console.log('🟢 SUCCESS: System prompt loaded for ID:', promptId, 'version:', result.version || 1);
        }
    } catch (error) {
        console.log('🔴 ERROR: Failed to load system prompt for ID:', error);
    }
}

async function initializeSession() {
    console.log('🔵 USER ACTION: initializeSession() called');
    if (isInitialized) {
        console.log('ℹ️ INFO: Already initialized, skipping');
        return;
    }

    console.log('🟡 STATUS: Initializing session...');
    showStatus('Initializing session...', 'info');

    try {
        console.log('🟡 API CALL: /api/init');
        const result = await apiCall('/api/init', 'POST');
        console.log('🟢 API RESPONSE: /api/init result:', result);

        if (result.success) {
            sessionId = result.session_id;
            isInitialized = true;
            console.log('🟢 SUCCESS: Session initialized with ID:', sessionId);
            showStatus(`✅ ${result.message}`, 'success');
            showSection('prompt-selection-section');
            showSection('system-prompt-section');
            showSection('user-input-section');
            showSection('ai-response-section');
            showSection('history-section');

            // Load existing prompt IDs after successful initialization
            await loadExistingPromptIds();
        } else {
            console.log('🔴 API ERROR: /api/init failed:', result.error);
            showStatus(`❌ ${result.error}`, 'error');
        }
    } catch (error) {
        console.log('🔴 EXCEPTION: Error in initializeSession:', error);
        showStatus(`❌ Error: ${error.message}`, 'error');
    }
}

async function askAI() {
    console.log('🔵 USER ACTION: askAI() called - FUNCTION START');
    const query = document.getElementById('user-query').value.trim();
    console.log('🔵 USER INPUT: query =', query);

    if (!query) {
        console.log('🔴 ERROR: No query provided');
        showStatus('Please enter a query', 'error');
        return;
    }

    console.log('🟢 SUCCESS: Query provided, proceeding with API calls');

    if (!isInitialized) {
        console.log('🔴 ERROR: Not initialized');
        showStatus('Please wait for initialization to complete', 'error');
        return;
    }

    console.log('🟢 SUCCESS: Initialization check passed');

    console.log('🟡 STATUS: Starting AI request...');
    setButtonLoading('ask-button', true);
    showStatus('Asking AI...', 'info');

    try {
        // Start conversation
        const requestData = { query };
        if (currentPromptId) {
            requestData.prompt_id = currentPromptId;
            console.log('🟡 API CALL: /api/start with query:', query, 'and custom prompt_id:', currentPromptId);
        } else {
            console.log('🟡 API CALL: /api/start with query:', query, '(auto-generated prompt_id)');
        }
        const startResult = await apiCall('/api/start', 'POST', requestData);
        console.log('🟢 API RESPONSE: /api/start result:', startResult);

        if (!startResult.success) {
            console.log('🔴 API ERROR: /api/start failed:', startResult.error);
            showStatus(`❌ ${startResult.error}`, 'error');
            return;
        }

        // Update prompts display
        console.log('🟡 UI UPDATE: Full startResult:', JSON.stringify(startResult, null, 2));
        console.log('🟡 UI UPDATE: Setting system prompt:', startResult.system_message);
        console.log('🟡 UI UPDATE: Setting user prompt:', startResult.user_message);
        console.log('🟡 UI UPDATE: System prompt length:', startResult.system_message ? startResult.system_message.length : 'null/undefined');
        document.getElementById('system-prompt').textContent = startResult.system_message || '(No system prompt received)';

        // User query is already displayed in the input field

        // Generate response
        console.log('🟡 API CALL: /api/generate');
        const responseResult = await apiCall('/api/generate', 'POST');
        console.log('🟢 API RESPONSE: /api/generate result:', responseResult);

        if (responseResult.success) {
            console.log('🟢 SUCCESS: AI response generated');
            showStatus('✅ AI response generated', 'success');
            document.getElementById('ai-response').textContent = responseResult.response;
            showSection('feedback-section');
        } else {
            console.log('🔴 API ERROR: /api/generate failed:', responseResult.error);
            showStatus(`❌ ${responseResult.error}`, 'error');
        }
    } catch (error) {
        console.log('🔴 EXCEPTION: Error in askAI:', error);
        showStatus(`❌ Error: ${error.message}`, 'error');
    } finally {
        console.log('🟡 UI UPDATE: Resetting button state');
        setButtonLoading('ask-button', false);
    }
}

async function processFeedback() {
    const feedback = document.getElementById('feedback-text').value.trim();
    console.log('🔵 USER ACTION: processFeedback() called');
    console.log('🔵 USER INPUT: feedback =', feedback);

    if (!feedback) {
        console.log('🔴 ERROR: No feedback provided');
        showStatus('Please provide feedback', 'error');
        return;
    }

    console.log('🟡 STATUS: Processing manual feedback...');
    showStatus('Processing feedback...', 'info');

    try {
        const promptId = currentPromptId || sessionId;
        console.log('🟡 API CALL: /api/feedback with feedback:', feedback, 'prompt_id:', promptId);
        const result = await apiCall('/api/feedback', 'POST', { feedback, prompt_id: promptId });
        console.log('🟢 API RESPONSE: /api/feedback result:', result);

        if (result.success) {
            console.log('🟢 SUCCESS: Feedback processed');
            showStatus('✅ Feedback processed successfully', 'success');

            // Clear the feedback input
            const feedbackInput = document.getElementById('feedback-text');
            if (feedbackInput) {
                feedbackInput.value = '';
                console.log('🟢 SUCCESS: Feedback input cleared');
            } else {
                console.log('🔴 ERROR: Feedback input element not found');
            }

            document.getElementById('feedback-display').innerHTML =
                `<div class="feedback-display">${result.feedback}</div>`;

            if (result.evolved) {
                console.log('🔄 EVOLUTION: System prompt evolved to version', result.version);
                console.log('🔄 EVOLUTION: New system message:', result.new_system_message);
                document.getElementById('evolution-notice').innerHTML =
                    `<div class="evolution-notice">🔄 System prompt evolved to version ${result.version}!</div>`;
                document.getElementById('system-prompt').textContent = result.new_system_message;

                // Update version display
                const versionDisplay = document.getElementById('prompt-version');
                versionDisplay.textContent = `(v${result.version})`;

                // Auto-generate new response with evolved prompt
                console.log('🔄 AUTO-GENERATE: Generating new response with evolved prompt...');
                showStatus('🔄 Generating new response with evolved prompt...', 'info');
                await generateNewResponse();
            } else {
                console.log('ℹ️ INFO: No evolution occurred');
            }
        } else {
            console.log('🔴 API ERROR: /api/feedback failed:', result.error);
            showStatus(`❌ ${result.error}`, 'error');
        }
    } catch (error) {
        console.log('🔴 EXCEPTION: Error in processFeedback:', error);
        showStatus(`❌ Error: ${error.message}`, 'error');
    }
}

async function processLLMFeedback() {
    console.log('🔵 USER ACTION: processLLMFeedback() called');

    // Get selected criteria
    const selectedCriteria = Array.from(
        document.querySelectorAll('input[type="checkbox"]:checked')
    ).map(cb => cb.value);

    // Get custom objective
    const customObjective = document.getElementById('custom-objective').value.trim();

    // Validate
    if (selectedCriteria.length === 0 && !customObjective) {
        console.log('🔴 ERROR: No evaluation criteria selected');
        showStatus('Please select at least one criteria or provide a custom objective', 'error');
        return;
    }

    console.log('🟡 EVALUATION: Selected criteria:', selectedCriteria);
    console.log('🟡 EVALUATION: Custom objective:', customObjective);
    console.log('🟡 STATUS: Generating AI feedback...');
    showStatus('Generating AI feedback...', 'info');

    try {
        const promptId = currentPromptId || sessionId;

        // Build evaluation request
        const evaluationRequest = {
            use_llm_feedback: true,
            criteria: selectedCriteria,
            custom_objective: customObjective,
            prompt_id: promptId
        };

        console.log('🟡 API CALL: /api/feedback with evaluation request:', evaluationRequest);
        const result = await apiCall('/api/feedback', 'POST', evaluationRequest);
        console.log('🟢 API RESPONSE: /api/feedback result:', result);

        if (result.success) {
            console.log('🟢 SUCCESS: AI feedback generated');
            showStatus('✅ AI feedback generated successfully', 'success');

            // Display the feedback with criteria info
            const criteriaText = selectedCriteria.length > 0 ? ` (${selectedCriteria.join(', ')})` : '';
            const objectiveText = customObjective ? ` | Objective: ${customObjective}` : '';
            document.getElementById('feedback-display').innerHTML =
                `<div class="feedback-display">🤖 AI Feedback${criteriaText}${objectiveText}: ${result.feedback}</div>`;

            if (result.evolved) {
                console.log('🔄 EVOLUTION: System prompt evolved to version', result.version);
                console.log('🔄 EVOLUTION: New system message:', result.new_system_message);
                document.getElementById('evolution-notice').innerHTML =
                    `<div class="evolution-notice">🔄 System prompt evolved to version ${result.version}!</div>`;
                document.getElementById('system-prompt').textContent = result.new_system_message;

                // Update version display
                const versionDisplay = document.getElementById('prompt-version');
                versionDisplay.textContent = `(v${result.version})`;

                // Auto-generate new response with evolved prompt
                console.log('🔄 AUTO-GENERATE: Generating new response with evolved prompt...');
                showStatus('🔄 Generating new response with evolved prompt...', 'info');
                await generateNewResponse();
            } else {
                console.log('ℹ️ INFO: No evolution occurred');
            }
        } else {
            console.log('🔴 API ERROR: /api/feedback failed:', result.error);
            showStatus(`❌ ${result.error}`, 'error');
        }
    } catch (error) {
        console.log('🔴 EXCEPTION: Error in processLLMFeedback:', error);
        showStatus(`❌ Error: ${error.message}`, 'error');
    }
}

async function generateNewResponse() {
    console.log('🔄 AUTO-GENERATE: Starting new response generation...');
    try {
        // Get the current user query from the input field
        const userQuery = document.getElementById('user-query').value.trim();
        console.log('🔄 AUTO-GENERATE: Using user query:', userQuery);

        if (!userQuery) {
            console.log('🔴 AUTO-GENERATE: No user query available');
            showStatus('❌ No user query available for new response', 'error');
            return;
        }

        // First, start a new conversation with the evolved prompt
        const requestData = { query: userQuery };
        if (currentPromptId) {
            requestData.prompt_id = currentPromptId;
            console.log('🔄 AUTO-GENERATE: Using custom prompt_id:', currentPromptId);
        } else {
            console.log('🔄 AUTO-GENERATE: Using auto-generated prompt_id');
        }

        const startResult = await apiCall('/api/start', 'POST', requestData);
        console.log('🟢 AUTO-GENERATE: /api/start result:', startResult);

        if (!startResult.success) {
            console.log('🔴 AUTO-GENERATE: /api/start failed:', startResult.error);
            showStatus(`❌ Failed to start new conversation: ${startResult.error}`, 'error');
            return;
        }

        // Then generate the response
        const responseResult = await apiCall('/api/generate', 'POST');
        console.log('🟢 AUTO-GENERATE: /api/generate result:', responseResult);

        if (responseResult.success) {
            console.log('🟢 AUTO-GENERATE: New response generated successfully');
            showStatus('✅ New response generated with evolved prompt!', 'success');
            document.getElementById('ai-response').textContent = responseResult.response;
        } else {
            console.log('🔴 AUTO-GENERATE: Failed to generate new response:', responseResult.error);
            showStatus(`❌ Failed to generate new response: ${responseResult.error}`, 'error');
        }
    } catch (error) {
        console.log('🔴 AUTO-GENERATE: Exception during new response generation:', error);
        showStatus(`❌ Error generating new response: ${error.message}`, 'error');
    }
}

async function loadHistory() {
    try {
        const result = await apiCall('/api/history');

        if (result.success) {
            const historyContent = document.getElementById('history-content');
            historyContent.innerHTML = `
                <div class="status info">
                    📊 Total interactions: ${result.history.length} |
                    Template versions: ${result.template_versions}
                </div>
            `;

            result.history.forEach((item, index) => {
                const historyItem = document.createElement('div');
                historyItem.className = 'history-item';
                historyItem.innerHTML = `
                    <h4>Interaction ${index + 1}</h4>
                    <div class="timestamp">${new Date(item.timestamp).toLocaleString()}</div>
                    <div class="content"><strong>Response:</strong> ${item.response}</div>
                    ${item.feedback ? `<div class="content"><strong>Feedback:</strong> ${item.feedback}</div>` : ''}
                    ${item.evaluation_score ? `<div class="content"><strong>Evaluation Score:</strong> ${item.evaluation_score}</div>` : ''}
                `;
                historyContent.appendChild(historyItem);
            });
        } else {
            document.getElementById('history-content').innerHTML =
                `<div class="status error">❌ ${result.error}</div>`;
        }
    } catch (error) {
        document.getElementById('history-content').innerHTML =
            `<div class="status error">❌ Error: ${error.message}</div>`;
    }
}
