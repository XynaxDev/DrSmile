document.addEventListener('DOMContentLoaded', function () {
    const conversationDiv = document.getElementById('conversation');
    const conversationContainer = document.getElementById('conversationContainer');
    const userInput = document.getElementById('userInput');
    const sendBtn = document.getElementById('sendBtn');
    const chatInputBar = document.getElementById('chatInputBar');
    const brandIcon = document.querySelector('.navbar-brand'); // Select the brand icon (DrSmile logo)

    userInput.addEventListener('keydown', function (e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // Auto-resize on input
    userInput.addEventListener('input', function () {
        autoResize();
        adjustConversationPadding();
    });

    // Scroll to bottom when the brand icon is clicked
    if (brandIcon) {
        brandIcon.addEventListener('click', function (e) {
            scrollToBottom();
        });
    }

    function autoResize() {
        userInput.style.height = '55px';
        let neededHeight = userInput.scrollHeight;
        if (neededHeight > 150) {
            neededHeight = 150;
            userInput.style.overflowY = 'auto';
        } else {
            userInput.style.overflowY = 'hidden';
        }
        userInput.style.height = neededHeight + 'px';
    }

    function adjustConversationPadding() {
        const barHeight = chatInputBar.offsetHeight;
        conversationContainer.style.paddingBottom = barHeight + 'px';
    }

    function sendMessage() {
        const message = userInput.value.trim();
        if (!message) return;

        fetch(chatbotAjaxUrl, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_input: message })
        })
            .then(response => response.json())
            .then(data => {
                if (data.messages) {
                    conversationDiv.innerHTML = renderMessages(data.messages);
                    userInput.value = '';
                    userInput.style.height = '55px';
                    adjustConversationPadding();
                    scrollToBottom();
                } else {
                    console.error('No messages found in response:', data);
                }
            })
            .catch(err => console.error('Error:', err));
    }

    function renderMessages(messages) {
        if (!messages || messages.length === 0) {
            return `
                <p class="text-center" style="font-size: 1.2rem; padding-top: 50px; color: #4e4e4e;">
                    <i>Your conversation will appear here...</i>
                </p>`;
        }

        let html = '';
        messages.forEach(msg => {
            // Ensure the message text is properly escaped to prevent rendering issues
            const safeText = msg.sender === 'user'
                ? escapeHtml(msg.text)
                : msg.text; // Bot messages are already escaped on the server

            if (msg.sender === 'user') {
                html += `
                <div class="chat-message user-message text-end mb-3">
                    <div class="alert alert-secondary d-inline-block chat-bubble border-0">
                        ${safeText}<br>
                        <small>${msg.time}</small>
                    </div>
                </div>`;
            } else {
                html += `
                <div class="chat-message bot-message d-flex align-items-start mb-3">
                    <img src="static/images/bot_avatar.png"
                        alt="Bot Logo"
                        class="rounded-circle me-2"
                        style="width: 40px; height: 40px;">
                    <div class="alert alert-info d-inline-block chat-bubble mb-0 border-0">
                        ${safeText}<br>
                        <small>${msg.time}</small>
                    </div>
                </div>`;
            }
        });
        return html;
    }

    // Function to escape HTML characters
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    function scrollToBottom() {
        setTimeout(() => {
            window.scrollTo(0, document.body.scrollHeight);
        }, 0);
    }

    adjustConversationPadding();
    scrollToBottom();
});