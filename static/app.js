// Global state
let sessionId = generateSessionId();
let isLoading = false;

const API_BASE = window.location.origin;

// ============================================================================
// Initialization
// ============================================================================

document.addEventListener('DOMContentLoaded', () => {
    updateSessionDisplay();
    checkHealth();
    document.getElementById('question-input').focus();
});

// ============================================================================
// Session Management
// ============================================================================

function generateSessionId() {
    return 'session_' + Math.random().toString(36).substr(2, 9) + '_' + Date.now();
}

function resetSession() {
    sessionId = generateSessionId();
    updateSessionDisplay();
    document.getElementById('chat-messages').innerHTML = `
        <div class="message assistant-message">
            <div class="message-avatar">⚡</div>
            <div class="message-content">
                <p>Session reset. Chat history cleared. Starting fresh conversation.</p>
            </div>
        </div>
    `;
}

function updateSessionDisplay() {
    document.getElementById('session-input').value = sessionId;
}

// ============================================================================
// Health Check
// ============================================================================

async function checkHealth() {
    try {
        const response = await fetch(`${API_BASE}/health`);
        const data = await response.json();

        const badge = document.getElementById('health-status');
        badge.className = 'status-badge status-healthy';
        badge.innerHTML = `<span class="status-dot"></span> Healthy`;

        console.log('Health check passed:', data);
    } catch (error) {
        const badge = document.getElementById('health-status');
        badge.className = 'status-badge status-error';
        badge.innerHTML = `<span class="status-dot"></span> Error`;
        console.error('Health check failed:', error);
    }
}

// ============================================================================
// Chat API
// ============================================================================

async function sendMessage() {
    const input = document.getElementById('question-input');
    const question = input.value.trim();

    if (!question || isLoading) return;

    isLoading = true;

    // Add user message
    addMessage('user', question);
    input.value = '';
    input.disabled = true;
    document.getElementById('send-btn').disabled = true;

    // Show loading indicator
    const loadingDiv = addLoadingMessage();

    try {
        const startTime = Date.now();

        const response = await fetch(`${API_BASE}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                question: question,
                session_id: sessionId
            })
        });

        const responseTime = Date.now() - startTime;
        updateResponseTime(responseTime);

        if (!response.ok) {
            const error = await response.json();
            addMessage('assistant', `Error: ${error.detail}`);
            return;
        }

        const data = await response.json();

        // Remove loading indicator
        loadingDiv.remove();

        // Add assistant response
        addMessage('assistant', data.answer);

        // Update preview
        updateResponsePreview(data.answer);

        // Check health periodically
        checkHealth();

    } catch (error) {
        loadingDiv.remove();
        addMessage('assistant', `Error: ${error.message}`);
        console.error('Chat error:', error);
    } finally {
        isLoading = false;
        input.disabled = false;
        document.getElementById('send-btn').disabled = false;
        input.focus();
    }
}

function askQuestion(question) {
    document.getElementById('question-input').value = question;
    sendMessage();
}

// ============================================================================
// UI Updates
// ============================================================================

function addMessage(role, content) {
    const messagesDiv = document.getElementById('chat-messages');

    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role === 'user' ? 'user-message' : 'assistant-message'}`;

    const avatar = role === 'user' ? '👤' : '⚡';
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.innerHTML = escapeHtml(content).split('\n').map(line => `<p>${line}</p>`).join('');

    messageDiv.innerHTML = `<div class="message-avatar">${avatar}</div>`;
    messageDiv.appendChild(contentDiv);

    messagesDiv.appendChild(messageDiv);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;

    return messageDiv;
}

function addLoadingMessage() {
    const messagesDiv = document.getElementById('chat-messages');

    const messageDiv = document.createElement('div');
    messageDiv.className = 'message assistant-message';
    messageDiv.innerHTML = `
        <div class="message-avatar">⚡</div>
        <div class="message-content">
            <div class="loading-indicator">
                <div class="dot"></div>
                <div class="dot"></div>
                <div class="dot"></div>
            </div>
        </div>
    `;

    messagesDiv.appendChild(messageDiv);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;

    return messageDiv;
}

function updateResponseTime(ms) {
    document.getElementById('response-time').textContent = `${ms}ms`;
}

function updateResponsePreview(text) {
    const preview = document.getElementById('response-preview');
    const truncated = text.length > 200 ? text.substring(0, 200) + '...' : text;
    preview.innerHTML = `<p>${escapeHtml(truncated)}</p>`;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ============================================================================
// Keyboard Shortcuts
// ============================================================================

document.addEventListener('keydown', (e) => {
    // Ctrl/Cmd + Enter to send
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        sendMessage();
    }

    // Ctrl/Cmd + K to focus input
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        document.getElementById('question-input').focus();
    }
});
