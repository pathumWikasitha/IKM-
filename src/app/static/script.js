const chatContainer = document.getElementById('chat-container');
const questionInput = document.getElementById('question-input');
const sendBtn = document.getElementById('send-btn');
const planningToggle = document.getElementById('planning-toggle');

// Auto-resize textarea
questionInput.addEventListener('input', function () {
    this.style.height = 'auto';
    this.style.height = (this.scrollHeight) + 'px';
    if (this.value === '') this.style.height = '50px';
});

// Handle send
async function handleSend() {
    const question = questionInput.value.trim();
    if (!question) return;

    // Add user message
    appendMessage(question, 'user');
    questionInput.value = '';
    questionInput.style.height = '50px';

    // Add loading state
    const loadingId = appendLoading();

    try {
        const response = await fetch('/qa', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                question: question,
                enable_planning: planningToggle.checked
            })
        });

        if (!response.ok) {
            throw new Error('Network response was not ok');
        }

        const data = await response.json();
        removeLoading(loadingId);
        appendBotResponse(data);

    } catch (error) {
        console.error('Error:', error);
        removeLoading(loadingId);
        appendMessage('Sorry, something went wrong. Please try again.', 'bot');
    }
}

sendBtn.addEventListener('click', handleSend);
questionInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleSend();
    }
});

function appendMessage(text, sender) {
    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${sender}-message`;
    msgDiv.innerHTML = `<div class="message-content">${text}</div>`;
    chatContainer.appendChild(msgDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

function appendLoading() {
    const id = 'loading-' + Date.now();
    const msgDiv = document.createElement('div');
    msgDiv.id = id;
    msgDiv.className = 'message bot-message';
    msgDiv.innerHTML = `
        <div class="message-content">
            <span class="loading-dots">Thinking...</span>
        </div>`;
    chatContainer.appendChild(msgDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight;
    return id;
}

function removeLoading(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
}

function appendBotResponse(data) {
    const msgDiv = document.createElement('div');
    msgDiv.className = 'message bot-message';

    let planHtml = '';
    if (data.plan) {
        planHtml = `
            <div class="plan-section">
                <div class="plan-title">⚡ Query Plan</div>
                <div class="plan-content">${data.plan}</div>
            </div>
        `;
    }

    let contextHtml = '';
    if (data.context) {
        const contextId = 'ctx-' + Date.now();
        contextHtml = `
            <div class="context-toggle" onclick="document.getElementById('${contextId}').classList.toggle('visible')">
                View Retrieved Context
            </div>
            <div id="${contextId}" class="context-section">
                <pre>${escapeHtml(data.context)}</pre>
            </div>
        `;
    }

    msgDiv.innerHTML = `
        ${planHtml}
        <div class="message-content">
            ${marked.parse(data.answer)}
        </div>
        ${contextHtml}
    `;

    chatContainer.appendChild(msgDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

// Simple markdown parser wrapper (using CDN in index.html would be better, but for now simple innerHTML or a very basic parser)
// Actually, let's inject title marked.js in index.html or just use textContent if marked is not available.
// For this environment, I'll assume I need to import it or just use simple text.
// Updated to just use text for safety if marked isn't loaded.

const marked = {
    parse: (text) => {
        // Very basic conversion
        return text
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\n/g, '<br>');
    }
};

function escapeHtml(text) {
    if (!text) return "";
    return text
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}
