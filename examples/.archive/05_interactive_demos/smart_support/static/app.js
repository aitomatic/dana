// Smart Customer Support Demo - JavaScript Application

class SupportDemo {
    constructor() {
        this.ws = null;
        this.demoTickets = [];
        this.isConnected = false;
        this.currentConversations = {
            basic: null,
            smart: null
        };
        
        this.initializeWebSocket();
        this.bindEventHandlers();
        this.loadDemoTickets();
    }

    // WebSocket Connection
    initializeWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws`;
        
        this.ws = new WebSocket(wsUrl);
        
        this.ws.onopen = () => {
            console.log('Connected to support demo server');
            this.isConnected = true;
            this.updateConnectionStatus(true);
        };
        
        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleWebSocketMessage(data);
        };
        
        this.ws.onclose = () => {
            console.log('Disconnected from support demo server');
            this.isConnected = false;
            this.updateConnectionStatus(false);
            
            // Attempt to reconnect after 3 seconds
            setTimeout(() => {
                if (!this.isConnected) {
                    this.initializeWebSocket();
                }
            }, 3000);
        };
        
        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            this.updateConnectionStatus(false);
        };
    }

    updateConnectionStatus(connected) {
        const statusElement = document.getElementById('connectionStatus');
        if (connected) {
            statusElement.textContent = '🟢 Connected';
            statusElement.style.color = '#27ae60';
        } else {
            statusElement.textContent = '🔴 Disconnected';
            statusElement.style.color = '#e74c3c';
        }
    }

    // Event Handlers
    bindEventHandlers() {
        // Demo ticket processing
        document.getElementById('processDemoTicket').addEventListener('click', () => {
            this.processDemoTicket();
        });

        // Custom ticket form
        document.getElementById('showCustomForm').addEventListener('click', () => {
            this.showCustomTicketForm();
        });

        document.getElementById('hideCustomForm').addEventListener('click', () => {
            this.hideCustomTicketForm();
        });

        document.getElementById('processCustomTicket').addEventListener('click', () => {
            this.processCustomTicket();
        });

        // Follow-up message handlers
        document.getElementById('sendBasicFollowUp').addEventListener('click', () => {
            this.sendFollowUp('basic');
        });

        document.getElementById('sendSmartFollowUp').addEventListener('click', () => {
            this.sendFollowUp('smart');
        });

        // Enter key handlers for follow-up textareas
        document.getElementById('basicFollowUp').addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendFollowUp('basic');
            }
        });

        document.getElementById('smartFollowUp').addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendFollowUp('smart');
            }
        });

        // Reset demo
        document.getElementById('resetDemo').addEventListener('click', () => {
            this.resetDemo();
        });
    }

    // Load demo tickets
    async loadDemoTickets() {
        try {
            const response = await fetch('/api/demo_tickets');
            const data = await response.json();
            this.demoTickets = data.tickets;
            this.populateTicketSelect();
        } catch (error) {
            console.error('Error loading demo tickets:', error);
        }
    }

    populateTicketSelect() {
        const select = document.getElementById('demoTicketSelect');
        select.innerHTML = '<option value="">Select a demo ticket...</option>';
        
        this.demoTickets.forEach(ticket => {
            const option = document.createElement('option');
            option.value = ticket.index;
            option.textContent = `${ticket.customer_name} - ${ticket.subject} (${ticket.sentiment})`;
            select.appendChild(option);
        });
    }

    // Process demo ticket
    processDemoTicket() {
        const select = document.getElementById('demoTicketSelect');
        const ticketIndex = parseInt(select.value);
        
        if (isNaN(ticketIndex)) {
            alert('Please select a demo ticket first');
            return;
        }

        this.showLoadingState();
        
        const message = {
            type: 'process_ticket',
            ticket_index: ticketIndex
        };

        this.ws.send(JSON.stringify(message));
    }

    // Custom ticket form
    showCustomTicketForm() {
        document.getElementById('customTicketForm').style.display = 'block';
        document.getElementById('customTicketForm').scrollIntoView({ behavior: 'smooth' });
    }

    hideCustomTicketForm() {
        document.getElementById('customTicketForm').style.display = 'none';
    }

    processCustomTicket() {
        const ticketData = {
            customer_name: document.getElementById('customerName').value,
            customer_tier: document.getElementById('customerTier').value,
            issue_type: document.getElementById('issueType').value,
            sentiment: document.getElementById('sentiment').value,
            urgency: document.getElementById('urgency').value,
            previous_contacts: parseInt(document.getElementById('previousContacts').value),
            technical_skill: document.getElementById('technicalSkill').value,
            subject: document.getElementById('subject').value,
            description: document.getElementById('description').value
        };

        // Validate required fields
        if (!ticketData.customer_name || !ticketData.subject || !ticketData.description) {
            alert('Please fill in all required fields');
            return;
        }

        this.showLoadingState();
        this.hideCustomTicketForm();

        const message = {
            type: 'process_custom_ticket',
            ticket_data: ticketData
        };

        this.ws.send(JSON.stringify(message));
    }

    // Show loading state
    showLoadingState() {
        document.getElementById('basicTicketDisplay').classList.add('loading');
        document.getElementById('smartTicketDisplay').classList.add('loading');
        document.getElementById('basicResponse').classList.add('loading');
        document.getElementById('smartResponse').classList.add('loading');
    }

    hideLoadingState() {
        document.getElementById('basicTicketDisplay').classList.remove('loading');
        document.getElementById('smartTicketDisplay').classList.remove('loading');
        document.getElementById('basicResponse').classList.remove('loading');
        document.getElementById('smartResponse').classList.remove('loading');
    }

    // Handle WebSocket messages
    handleWebSocketMessage(data) {
        switch (data.type) {
            case 'ticket_processed':
                this.displayTicketResults(data);
                break;
            case 'follow_up_processed':
                this.displayFollowUpResults(data);
                break;
            case 'metrics_update':
                this.updateMetrics(data);
                break;
            default:
                console.log('Unknown message type:', data.type);
        }
    }

    // Display ticket processing results
    displayTicketResults(data) {
        this.hideLoadingState();
        
        // Display ticket information
        this.displayTicketInfo(data.ticket);
        
        // Display responses
        this.displayResponse('basic', data.basic_result);
        this.displayResponse('smart', data.smart_result);
        
        // Update metrics
        this.updateSystemMetrics('basic', data.basic_result);
        this.updateSystemMetrics('smart', data.smart_result);
        
        // Store conversation IDs and show conversation areas
        if (data.conversation_ids) {
            this.currentConversations.basic = data.conversation_ids.basic;
            this.currentConversations.smart = data.conversation_ids.smart;
            this.showConversationAreas();
        }
    }

    displayTicketInfo(ticket) {
        const ticketHTML = `
            <div class="ticket-info">
                <div class="ticket-header">
                    <span class="ticket-id">${ticket.ticket_id}</span>
                    <div class="customer-info">
                        <strong>${ticket.customer_name}</strong>
                        <span class="tier-badge tier-${ticket.customer_tier}">${ticket.customer_tier}</span>
                        <span class="sentiment-badge sentiment-${ticket.sentiment}">${ticket.sentiment.replace('_', ' ')}</span>
                    </div>
                </div>
                <div class="ticket-subject">${ticket.subject}</div>
                <div class="ticket-description">${ticket.description}</div>
                <div class="ticket-metadata">
                    <small>Type: ${ticket.issue_type} | Urgency: ${ticket.urgency} | Previous contacts: ${ticket.previous_contacts}</small>
                </div>
            </div>
        `;
        
        document.getElementById('basicTicketDisplay').innerHTML = ticketHTML;
        document.getElementById('smartTicketDisplay').innerHTML = ticketHTML;
    }

    displayResponse(system, result) {
        const responseHTML = `
            <div class="response-content">
                <div class="response-text">${result.response_text}</div>
                <div class="response-metadata">
                    <div class="metadata-item">
                        <span class="metadata-label">Tone</span>
                        <span class="metadata-value">${result.tone}</span>
                    </div>
                    <div class="metadata-item">
                        <span class="metadata-label">Escalation</span>
                        <span class="metadata-value ${result.escalation_recommended ? 'escalation-yes' : 'escalation-no'}">
                            ${result.escalation_recommended ? 'Yes' : 'No'}
                        </span>
                    </div>
                    <div class="metadata-item">
                        <span class="metadata-label">Resolution Time</span>
                        <span class="metadata-value">${result.estimated_resolution_time}</span>
                    </div>
                    <div class="metadata-item">
                        <span class="metadata-label">Confidence</span>
                        <span class="metadata-value">${(result.confidence_score * 100).toFixed(1)}%</span>
                    </div>
                    <div class="metadata-item">
                        <span class="metadata-label">Satisfaction Score</span>
                        <span class="metadata-value">${result.satisfaction_score.toFixed(1)}/5.0</span>
                    </div>
                </div>
                <div class="response-reasoning">
                    <small><strong>Reasoning:</strong> ${result.reasoning}</small>
                </div>
            </div>
        `;
        
        document.getElementById(`${system}Response`).innerHTML = responseHTML;
    }

    updateSystemMetrics(system, result) {
        // This will be updated when we receive the full metrics update
        // For now, just show the current result metrics
        document.getElementById(`${system}Satisfaction`).textContent = `${result.satisfaction_score.toFixed(1)}/5`;
    }

    // Update metrics from server
    updateMetrics(data) {
        // Update basic system metrics
        if (data.basic_metrics) {
            const basic = data.basic_metrics;
            document.getElementById('basicSatisfaction').textContent = 
                basic.total_tickets > 0 ? `${basic.avg_satisfaction.toFixed(1)}/5` : '-';
            document.getElementById('basicEscalation').textContent = 
                basic.total_tickets > 0 ? `${(basic.escalation_rate * 100).toFixed(1)}%` : '-';
            document.getElementById('basicResolution').textContent = 
                basic.total_tickets > 0 ? `${basic.avg_resolution_time.toFixed(1)}h` : '-';
        }

        // Update smart system metrics
        if (data.smart_metrics) {
            const smart = data.smart_metrics;
            document.getElementById('smartSatisfaction').textContent = 
                smart.total_tickets > 0 ? `${smart.avg_satisfaction.toFixed(1)}/5` : '-';
            document.getElementById('smartEscalation').textContent = 
                smart.total_tickets > 0 ? `${(smart.escalation_rate * 100).toFixed(1)}%` : '-';
            document.getElementById('smartResolution').textContent = 
                smart.total_tickets > 0 ? `${smart.avg_resolution_time.toFixed(1)}h` : '-';
        }

        // Update POET learning status
        if (data.poet_status && data.poet_status.status !== "POET not available") {
            this.updateLearningDashboard(data.poet_status);
        }
    }

    updateLearningDashboard(poetStatus) {
        // Update learning status
        document.getElementById('learningStatusText').textContent = poetStatus.status || 'Learning in progress...';
        document.getElementById('learningExecutions').textContent = poetStatus.executions || 0;
        document.getElementById('learningAccuracy').textContent = 
            `${((poetStatus.context_accuracy || 0.6) * 100).toFixed(0)}%`;
        document.getElementById('learningTone').textContent = 
            `${((poetStatus.tone_matching || 0.5) * 100).toFixed(0)}%`;

        // Update recommendations
        if (poetStatus.recommendations) {
            const list = document.getElementById('recommendationsList');
            list.innerHTML = '';
            poetStatus.recommendations.forEach(rec => {
                const li = document.createElement('li');
                li.textContent = rec;
                list.appendChild(li);
            });
        }

        // Update performance improvements
        if (poetStatus.escalation_rate !== undefined) {
            document.getElementById('currentEscalationRate').textContent = 
                `${(poetStatus.escalation_rate * 100).toFixed(0)}%`;
        }

        if (poetStatus.metrics && poetStatus.metrics.avg_satisfaction !== undefined) {
            document.getElementById('currentSatisfaction').textContent = 
                `${poetStatus.metrics.avg_satisfaction.toFixed(1)}/5`;
        }
    }

    // Reset demo
    async resetDemo() {
        if (!confirm('Are you sure you want to reset the demo? This will clear all progress.')) {
            return;
        }

        try {
            const response = await fetch('/api/reset', { method: 'POST' });
            if (response.ok) {
                // Clear displays
                document.getElementById('basicTicketDisplay').innerHTML = `
                    <div class="placeholder-content">
                        <i class="fas fa-ticket-alt"></i>
                        <p>Select a ticket to see how basic AI support handles it</p>
                    </div>
                `;
                document.getElementById('smartTicketDisplay').innerHTML = `
                    <div class="placeholder-content">
                        <i class="fas fa-ticket-alt"></i>
                        <p>Select a ticket to see how POET-enhanced support handles it</p>
                    </div>
                `;
                document.getElementById('basicResponse').innerHTML = `
                    <div class="placeholder-content">
                        <i class="fas fa-comment-dots"></i>
                        <p>Response will appear here</p>
                    </div>
                `;
                document.getElementById('smartResponse').innerHTML = `
                    <div class="placeholder-content">
                        <i class="fas fa-lightbulb"></i>
                        <p>Intelligent response will appear here</p>
                    </div>
                `;

                // Reset metrics
                ['basicSatisfaction', 'basicEscalation', 'basicResolution',
                 'smartSatisfaction', 'smartEscalation', 'smartResolution'].forEach(id => {
                    document.getElementById(id).textContent = '-';
                });

                // Reset learning dashboard
                document.getElementById('learningStatusText').textContent = 'Initializing learning system...';
                document.getElementById('learningExecutions').textContent = '0';
                document.getElementById('learningAccuracy').textContent = '60%';
                document.getElementById('learningTone').textContent = '50%';
                document.getElementById('recommendationsList').innerHTML = '<li>Collecting initial performance data...</li>';
                document.getElementById('currentEscalationRate').textContent = '25%';
                document.getElementById('currentSatisfaction').textContent = '3.0/5';

                // Reset conversations
                this.currentConversations.basic = null;
                this.currentConversations.smart = null;
                document.getElementById('basicConversation').style.display = 'none';
                document.getElementById('smartConversation').style.display = 'none';
                document.getElementById('basicMessages').innerHTML = '';
                document.getElementById('smartMessages').innerHTML = '';
                document.getElementById('basicFollowUp').value = '';
                document.getElementById('smartFollowUp').value = '';

                // Reset form
                document.getElementById('demoTicketSelect').value = '';
                this.hideCustomTicketForm();

                alert('Demo reset successfully!');
            }
        } catch (error) {
            console.error('Error resetting demo:', error);
            alert('Error resetting demo. Please try again.');
        }
    }

    // Follow-up conversation methods
    showConversationAreas() {
        document.getElementById('basicConversation').style.display = 'block';
        document.getElementById('smartConversation').style.display = 'block';
    }

    sendFollowUp(system) {
        const textareaId = `${system}FollowUp`;
        const textarea = document.getElementById(textareaId);
        const followUpText = textarea.value.trim();
        
        if (!followUpText) {
            alert('Please enter a follow-up message');
            return;
        }

        const conversationId = this.currentConversations[system];
        if (!conversationId) {
            alert('No active conversation found');
            return;
        }

        // Clear textarea and disable button temporarily
        textarea.value = '';
        const button = document.getElementById(`send${system.charAt(0).toUpperCase() + system.slice(1)}FollowUp`);
        button.disabled = true;
        button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Sending...';

        // Add customer message to conversation immediately
        this.addMessageToConversation(system, 'customer', followUpText);

        // Send via WebSocket
        const message = {
            type: 'send_follow_up',
            conversation_id: conversationId,
            follow_up_text: followUpText
        };

        this.ws.send(JSON.stringify(message));

        // Re-enable button after a short delay
        setTimeout(() => {
            button.disabled = false;
            button.innerHTML = '<i class="fas fa-paper-plane"></i> Send Follow-up';
        }, 1000);
    }

    displayFollowUpResults(data) {
        const conversationId = data.conversation_id;
        
        // Add agent responses to both conversations
        this.addMessageToConversation('basic', 'agent', data.basic_result.response_text, {
            tone: data.basic_result.tone,
            escalation: data.basic_result.escalation_recommended,
            satisfaction: data.basic_result.satisfaction_score
        });
        
        this.addMessageToConversation('smart', 'agent', data.smart_result.response_text, {
            tone: data.smart_result.tone,
            escalation: data.smart_result.escalation_recommended,
            satisfaction: data.smart_result.satisfaction_score
        });
    }

    addMessageToConversation(system, sender, text, metadata = {}) {
        const messagesContainer = document.getElementById(`${system}Messages`);
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}`;
        
        const currentTime = new Date().toLocaleTimeString();
        const senderName = sender === 'customer' ? 'Customer' : `${system.charAt(0).toUpperCase() + system.slice(1)} Support`;
        
        let metadataHTML = '';
        if (sender === 'agent' && metadata.tone) {
            metadataHTML = `
                <div class="message-metadata">
                    <span>Tone: ${metadata.tone}</span>
                    ${metadata.escalation ? ' | <span class="escalation-yes">Escalated</span>' : ' | <span class="escalation-no">No escalation</span>'}
                    | Satisfaction: ${metadata.satisfaction?.toFixed(1)}/5
                </div>
            `;
        }
        
        messageDiv.innerHTML = `
            <div class="message-header">
                <span class="message-sender">${senderName}</span>
                <span class="message-time">${currentTime}</span>
            </div>
            <div class="message-text">${text}</div>
            ${metadataHTML}
        `;
        
        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    // Utility methods
    formatPercentage(value) {
        return `${(value * 100).toFixed(1)}%`;
    }

    formatScore(value, max = 5) {
        return `${value.toFixed(1)}/${max}`;
    }

    formatTime(hours) {
        if (hours < 1) {
            return `${(hours * 60).toFixed(0)}m`;
        } else if (hours < 24) {
            return `${hours.toFixed(1)}h`;
        } else {
            return `${(hours / 24).toFixed(1)}d`;
        }
    }
}

// Initialize the demo when the page loads
document.addEventListener('DOMContentLoaded', () => {
    window.supportDemo = new SupportDemo();
});

// Handle page visibility changes to manage WebSocket connection
document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
        // Page is hidden, potentially pause updates
        console.log('Page hidden, maintaining connection');
    } else {
        // Page is visible, ensure connection is active
        if (window.supportDemo && !window.supportDemo.isConnected) {
            console.log('Page visible, reconnecting...');
            window.supportDemo.initializeWebSocket();
        }
    }
});

// Add some helpful console messages
console.log('🎧 Smart Customer Support Demo loaded');
console.log('💡 This demo shows how POET learns to optimize customer support prompts');
console.log('🚀 Try different tickets to see the learning in action!');