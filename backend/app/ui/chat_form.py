"""HTML renderer for the chat streaming playground."""


def render_chat_form() -> str:
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8" />
        <title>Local LLM Chat</title>
        <style>
            :root {
                color-scheme: light dark;
            }
            body {
                margin: 0;
                font-family: "Segoe UI", system-ui, -apple-system, sans-serif;
                background: #f4f5f8;
                color: #1f2933;
            }
            main {
                max-width: 820px;
                margin: 0 auto;
                padding: 2.5rem 1.5rem 3rem;
            }
            h1 {
                font-size: 2rem;
                margin-bottom: 0.25rem;
            }
            p.description {
                margin-top: 0;
                margin-bottom: 1.5rem;
                color: #4b5563;
            }
            .panel {
                background: white;
                border-radius: 18px;
                padding: 1.75rem;
                box-shadow: 0 20px 40px rgba(15, 23, 42, 0.08);
            }
            textarea {
                width: 100%;
                box-sizing: border-box;
                border-radius: 12px;
                border: 1px solid #d0d5dd;
                background: white;
                color: inherit;
                font-size: 1rem;
                padding: 0.85rem 1rem;
                resize: vertical;
            }
            textarea:focus {
                outline: none;
                border-color: #2563eb;
                box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.2);
            }
            .config {
                margin-bottom: 1.5rem;
            }
            .config label {
                font-size: 0.9rem;
                font-weight: 600;
                color: #374151;
                display: block;
                margin-bottom: 0.5rem;
            }
            .messages {
                display: flex;
                flex-direction: column;
                gap: 1rem;
                max-height: 420px;
                min-height: 240px;
                overflow-y: auto;
                padding: 1rem;
                margin-bottom: 1.5rem;
                border: 1px solid #d0d5dd;
                border-radius: 16px;
                background: linear-gradient(180deg, rgba(89, 126, 247, 0.08), rgba(226, 232, 240, 0.35));
                box-shadow: inset 0 1px 2px rgba(15, 23, 42, 0.04);
            }
            .message {
                padding: 0.85rem 1rem;
                border-radius: 14px;
                line-height: 1.5;
                white-space: pre-wrap;
                word-break: break-word;
            }
            .message.user {
                align-self: flex-end;
                background: #2563eb;
                color: white;
            }
            .message.assistant {
                align-self: flex-start;
                background: #e2e8f0;
                color: #111827;
            }
            .message.system {
                align-self: center;
                background: #cbd5f5;
                color: #1e3a8a;
            }
            form#chatForm {
                display: flex;
                flex-direction: column;
                gap: 0.75rem;
            }
            form#chatForm textarea {
                min-height: 120px;
            }
            .actions {
                display: flex;
                gap: 0.75rem;
            }
            button {
                appearance: none;
                border: none;
                border-radius: 999px;
                padding: 0.75rem 1.5rem;
                font-size: 1rem;
                font-weight: 600;
                cursor: pointer;
                transition: transform 0.15s ease, box-shadow 0.15s ease;
            }
            button.primary {
                background: #2563eb;
                color: white;
                box-shadow: 0 10px 20px rgba(37, 99, 235, 0.25);
            }
            button.secondary {
                background: #e5e7eb;
                color: #111827;
            }
            button:disabled {
                opacity: 0.65;
                cursor: not-allowed;
                transform: none;
                box-shadow: none;
            }
            button:not(:disabled):hover {
                transform: translateY(-1px);
            }
            .sr-only {
                position: absolute;
                width: 1px;
                height: 1px;
                padding: 0;
                margin: -1px;
                overflow: hidden;
                clip: rect(0, 0, 0, 0);
                border: 0;
            }
            #statusBar {
                min-height: 1.2rem;
                font-size: 0.9rem;
                color: #4b5563;
            }
            .error-text {
                color: #dc2626;
            }
            @media (prefers-color-scheme: dark) {
                body {
                    background: #0f172a;
                    color: #e2e8f0;
                }
                .panel {
                    background: #111827;
                    box-shadow: none;
                }
                textarea {
                    background: #0f172a;
                    border-color: #334155;
                }
                .messages {
                    border-color: #2f3b55;
                    background: linear-gradient(180deg, rgba(59, 130, 246, 0.15), rgba(15, 23, 42, 0.75));
                    box-shadow: inset 0 1px 2px rgba(15, 23, 42, 0.4);
                }
                .message.assistant {
                    background: rgba(30, 41, 59, 0.8);
                    color: #f1f5f9;
                }
                .message.user {
                    background: #3b82f6;
                }
                .message.system {
                    background: #3730a3;
                    color: #ede9fe;
                }
                button.secondary {
                    background: #1f2937;
                    color: #f3f4f6;
                }
            }
        </style>
    </head>
    <body>
        <main>
            <div class="panel">
                <h1>Local LLM Chat</h1>
                <p class="description">Chat with your local OpenAI-compatible model. Replies stream live so you can follow along.</p>
                <div class="config">
                    <label for="systemPrompt">System prompt</label>
                    <textarea id="systemPrompt" rows="2">You are a friendly English tutor. Keep replies clear and concise.</textarea>
                </div>
                <section id="messages" class="messages" aria-live="polite"></section>
                <form id="chatForm">
                    <label for="userInput" class="sr-only">Message</label>
                    <textarea id="userInput" placeholder="Ask the assistant something in English..." required></textarea>
                    <div class="actions">
                        <button type="submit" id="sendBtn" class="primary">Send</button>
                        <button type="button" id="resetBtn" class="secondary">Reset conversation</button>
                    </div>
                </form>
                <div id="statusBar"></div>
            </div>
        </main>
        <script>
            const messages = [];

            const systemPromptEl = document.getElementById('systemPrompt');
            const messagesContainer = document.getElementById('messages');
            const chatForm = document.getElementById('chatForm');
            const userInput = document.getElementById('userInput');
            const sendBtn = document.getElementById('sendBtn');
            const resetBtn = document.getElementById('resetBtn');
            const statusBar = document.getElementById('statusBar');

            function addMessage(role, text) {
                const bubble = document.createElement('div');
                bubble.className = `message ${role}`;
                bubble.textContent = text;
                messagesContainer.appendChild(bubble);
                messagesContainer.scrollTop = messagesContainer.scrollHeight;
                return bubble;
            }

            function ensureSystemPrompt() {
                const prompt = systemPromptEl.value.trim();
                if (!prompt) {
                    return;
                }
                if (messages.length === 0 || messages[0].role !== 'system') {
                    messages.unshift({ role: 'system', content: prompt });
                } else {
                    messages[0].content = prompt;
                }
            }

            function resetConversation() {
                messages.length = 0;
                messagesContainer.innerHTML = '';
                statusBar.textContent = 'Idle';
                sendBtn.disabled = false;
                const prompt = systemPromptEl.value.trim();
                if (prompt) {
                    addMessage('system', prompt);
                }
                ensureSystemPrompt();
            }

            resetBtn.addEventListener('click', () => {
                resetConversation();
                userInput.focus();
            });

            chatForm.addEventListener('submit', async (event) => {
                event.preventDefault();
                const text = userInput.value.trim();
                if (!text) {
                    return;
                }

                ensureSystemPrompt();
                const userBubble = addMessage('user', text);
                userBubble.dataset.role = 'user';
                messages.push({ role: 'user', content: text });
                userInput.value = '';

                sendBtn.disabled = true;
                statusBar.textContent = 'Streaming response...';

                const assistantBubble = addMessage('assistant', '');
                let assistantText = '';

                try {
                    const payload = {
                        messages: messages.map((m) => ({ role: m.role, content: m.content })),
                    };
                    const response = await fetch('/chat/stream', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify(payload),
                    });

                    if (!response.ok || !response.body) {
                        throw new Error(`HTTP ${response.status}`);
                    }

                    const reader = response.body.getReader();
                    const decoder = new TextDecoder('utf-8');
                    let buffer = '';
                    let doneStreaming = false;

                    const processEvent = (rawEvent) => {
                        if (!rawEvent) {
                            return false;
                        }

                        const dataSegments = [];
                        const lines = rawEvent.split('\\n');
                        for (const rawLine of lines) {
                            const line = rawLine.trim();
                            if (!line || line.startsWith(':')) {
                                continue;
                            }
                            if (!line.startsWith('data:')) {
                                continue;
                            }
                            const value = line.slice(5).trim();
                            if (!value) {
                                continue;
                            }
                            if (value === '[DONE]') {
                                return true;
                            }
                            dataSegments.push(value);
                        }

                        if (dataSegments.length === 0) {
                            return false;
                        }

                        const jsonStr = dataSegments.join('\\n');
                        let parsed;
                        try {
                            parsed = JSON.parse(jsonStr);
                        } catch (error) {
                            console.error('Failed to parse SSE chunk', error, jsonStr);
                            return false;
                        }
                        if (parsed.error) {
                            throw new Error(parsed.error);
                        }
                        const choice = (parsed.choices && parsed.choices[0]) || {};
                        const delta = choice.delta || {};
                        if (delta.content) {
                            assistantText += delta.content;
                            assistantBubble.textContent = assistantText;
                            messagesContainer.scrollTop = messagesContainer.scrollHeight;
                        }
                        if (choice.finish_reason) {
                            return true;
                        }
                        return false;
                    };

                    while (!doneStreaming) {
                        const { value, done } = await reader.read();
                        if (done) {
                            buffer += decoder.decode();
                            break;
                        }
                        buffer += decoder.decode(value, { stream: true });
                        const events = buffer.split('\\n\\n');
                        buffer = events.pop();

                        for (const rawEvent of events) {
                            if (processEvent(rawEvent)) {
                                doneStreaming = true;
                                break;
                            }
                        }
                    }

                    if (!doneStreaming && buffer) {
                        if (processEvent(buffer)) {
                            doneStreaming = true;
                        }
                    }
                } catch (error) {
                    console.error(error);
                    assistantBubble.classList.add('error-text');
                    assistantBubble.textContent = `Error: ${error.message || error}`;
                    statusBar.textContent = 'An error occurred. Check console for details.';
                    sendBtn.disabled = false;
                    userInput.focus();
                    return;
                }

                const finalText = assistantText.trim();
                assistantBubble.textContent = finalText || '[empty reply]';
                assistantBubble.classList.remove('error-text');
                messages.push({ role: 'assistant', content: finalText });
                statusBar.textContent = 'Idle';
                sendBtn.disabled = false;
                userInput.focus();
            });

            // Prime the conversation with the default system prompt for visibility.
            resetConversation();
        </script>
    </body>
    </html>
    """
