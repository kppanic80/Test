// Constants
const API_ENDPOINTS = {
    CHAT: '/api/chat',
    CBI: '/api/cbi'
};

const URLS = {
    CFTDTI: 'https://www.canada.ca/en/department-national-defence/services/benefits-military/pay-pension-benefits/benefits/canadian-forces-temporary-duty-travel-instructions.html',
    CBI: 'https://www.canada.ca/en/department-national-defence/corporate/policies-standards/compensation-benefits-instructions.html'
};

// DOM Elements
const elements = {
    simplifyToggle: document.getElementById('simplify-toggle'),
    chatBox: document.getElementById('chat-box'),
    userInput: document.getElementById('user-input'),
    sendButton: document.getElementById('send-button'),
    progressBar: document.getElementById('progress-bar'),
    darkModeToggle: document.getElementById('dark-mode-toggle'),
    typingIndicator: document.getElementById('typing-indicator'),
    urlInput: document.getElementById('url-input'),
    loadUrlButton: document.getElementById('load-url-button'),
    cftdtiToggle: document.getElementById('cftdti-toggle'),
    cbiToggle: document.getElementById('cbi-toggle'),
    suggestedQuestions: document.getElementById('suggested-questions')
};

// State
let state = {
    parsedContent: null,
    sentences: [],
    isLoading: false,
    currentPolicy: null
};

// Helper Functions
function appendMessage(content, className) {
    const messageElement = document.createElement('div');
    messageElement.className = className;
    messageElement.innerHTML = parseMarkdown(content);
    elements.chatBox.appendChild(messageElement);
    elements.chatBox.scrollTop = elements.chatBox.scrollHeight;
}

function parseMarkdown(text) {
    return text
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/\$\$([^$$]+)\$\$\$\$([^)]+)\$\$/g, '<a href="$2" target="_blank">$1</a>')
        .replace(/\n/g, '<br>')
        .replace(/\s*\*\s*/g, '');
}

function updateProgressBar(value) {
    elements.progressBar.style.width = `${value}%`;
    elements.progressBar.setAttribute('aria-valuenow', value);
}

function setLoading(isLoading) {
    state.isLoading = isLoading;
    elements.sendButton.disabled = isLoading;
    elements.loadUrlButton.disabled = isLoading;
    elements.typingIndicator.style.display = isLoading ? 'block' : 'none';
    updateProgressBar(isLoading ? 20 : 0);
}

async function fetchWithTimeout(url, options, timeout = 10000) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);

    try {
        const response = await fetch(url, {
            ...options,
            signal: controller.signal
        });
        clearTimeout(timeoutId);
        return response;
    } catch (error) {
        clearTimeout(timeoutId);
        throw error;
    }
}

async function handleApiResponse(response) {
    const responseText = await response.text();
    console.log('Raw response:', responseText);

    try {
        const data = JSON.parse(responseText);
        if (!response.ok) {
            throw new Error(data.error || 'Server error');
        }
        return data;
    } catch (e) {
        console.error('Failed to parse JSON:', e);
        throw new Error('Invalid server response');
    }
}

// Suggested Questions Functions
async function generateSuggestedQuestions(content) {
    try {
        const response = await fetchWithTimeout(
            API_ENDPOINTS.CHAT + '?action=suggest',
            {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                body: JSON.stringify({
                    content: content
                })
            }
        );

        const data = await handleApiResponse(response);
        return data.questions;
    } catch (error) {
        console.error('Error generating questions:', error);
        return [
            "Can you summarize this document?",
            "What are the main points?",
            "What are the key requirements?"
        ];
    }
}

async function displaySuggestedQuestions(questions) {
    elements.suggestedQuestions.innerHTML = '';
    
    questions.forEach(question => {
        const button = document.createElement('button');
        button.className = 'suggested-question';
        button.textContent = question;
        button.addEventListener('click', () => {
            elements.userInput.value = question;
            elements.userInput.focus();
        });
        elements.suggestedQuestions.appendChild(button);
    });
}

// Core Functions
async function fetchAndParseContent(url) {
    try {
        const response = await fetchWithTimeout(url, {
            method: 'GET',
            headers: {
                'Accept': 'text/html'
            }
        });

        if (!response.ok) {
            throw new Error(`Failed to fetch content: ${response.statusText}`);
        }

        const html = await response.text();
        const parser = new DOMParser();
        const doc = parser.parseFromString(html, 'text/html');
        const textContent = doc.body.innerText;
        return {
            textContent,
            characterCount: textContent.length
        };
    } catch (error) {
        console.error('Error fetching content:', error);
        throw error;
    }
}

function preprocessContent(content) {
    state.sentences = (content.match(/[^\.!\?]+[\.!\?]+/g) || [content])
        .map(sentence => ({
            text: sentence.trim(),
            words: sentence.toLowerCase().match(/\b(\w+)\b/g) || []
        }));
}

async function sendMessage() {
    const userMessage = elements.userInput.value.trim();
    if (!userMessage || state.isLoading) return;

    appendMessage(userMessage, 'user-message');
    elements.userInput.value = '';
    setLoading(true);

    try {
        const response = await fetchWithTimeout(
            API_ENDPOINTS.CHAT,
            {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                body: JSON.stringify({
                    question: userMessage,
                    content: state.parsedContent,
                    url: elements.cftdtiToggle.checked ? URLS.CFTDTI : 
                         (elements.cbiToggle.checked ? URLS.CBI : 
                         elements.urlInput.value.trim()),
                    simplify: elements.simplifyToggle.checked
                })
            }
        );

        const data = await handleApiResponse(response);
        appendMessage(data.response, 'bot-message');
    } catch (error) {
        console.error('Error:', error);
        appendMessage(`Error: ${error.message}`, 'bot-message');
    } finally {
        setLoading(false);
    }
}

async function loadUrlContent() {
    const url = elements.urlInput.value.trim();
    if (!url || state.isLoading) return;

    appendMessage(`Loading content from ${url}...`, 'user-message');
    elements.urlInput.value = '';
    setLoading(true);

    try {
        const result = await fetchAndParseContent(url);
        state.parsedContent = result.textContent;
        preprocessContent(state.parsedContent);
        
        // Generate and display suggested questions
        const questions = await generateSuggestedQuestions(state.parsedContent);
        displaySuggestedQuestions(questions);

        appendMessage(
            `Content loaded successfully. ${result.characterCount} characters parsed. You can now ask questions.`,
            'bot-message'
        );
    } catch (error) {
        appendMessage(`Error: ${error.message}`, 'bot-message');
    } finally {
        setLoading(false);
    }
}

// Event Handlers
elements.loadUrlButton.addEventListener('click', loadUrlContent);

elements.cftdtiToggle.addEventListener('change', function() {
    if (this.checked) {
        elements.cbiToggle.checked = false;
        elements.urlInput.value = URLS.CFTDTI;
        state.currentPolicy = 'cftdti';
        loadUrlContent();
    } else {
        elements.urlInput.value = '';
        state.currentPolicy = null;
        displaySuggestedQuestions([
            "Can you summarize this document?",
            "What are the main points?",
            "What are the key requirements?"
        ]);
    }
});

elements.cbiToggle.addEventListener('change', async function() {
    if (this.checked) {
        elements.cftdtiToggle.checked = false;
        elements.urlInput.value = URLS.CBI;
        appendMessage('Loading CBI content...', 'user-message');
        setLoading(true);

        try {
            const response = await fetchWithTimeout(API_ENDPOINTS.CBI);
            const data = await handleApiResponse(response);
            state.parsedContent = data.content;
            preprocessContent(state.parsedContent);
            
            // Generate and display suggested questions
            const questions = await generateSuggestedQuestions(state.parsedContent);
            displaySuggestedQuestions(questions);

            appendMessage(
                `CBI content loaded successfully. ${data.content.length} characters parsed. You can now ask questions.`,
                'bot-message'
            );
        } catch (error) {
            appendMessage(`Error: ${error.message}`, 'bot-message');
        } finally {
            setLoading(false);
        }
    } else {
        elements.urlInput.value = '';
        state.parsedContent = null;
        displaySuggestedQuestions([
            "Can you summarize this document?",
            "What are the main points?",
            "What are the key requirements?"
        ]);
    }
});

elements.sendButton.addEventListener('click', sendMessage);

elements.userInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') sendMessage();
});

elements.darkModeToggle.addEventListener('click', () => {
    document.body.classList.toggle('dark-mode');
    elements.darkModeToggle.textContent = 
        document.body.classList.contains('dark-mode') ? 'Light Mode' : 'Dark Mode';
});

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    // Check system dark mode preference
    if (window.matchMedia && 
        window.matchMedia('(prefers-color-scheme: dark)').matches) {
        document.body.classList.add('dark-mode');
        elements.darkModeToggle.textContent = 'Light Mode';
    }

    // Display default suggested questions
    displaySuggestedQuestions([
        "Can you summarize this document?",
        "What are the main points?",
        "What are the key requirements?"
    ]);

    // Focus input field
    elements.userInput.focus();
});

// Error handling for missing elements
Object.entries(elements).forEach(([key, element]) => {
    if (!element) {
        console.error(`Missing DOM element: ${key}`);
    }
});
