document.addEventListener('DOMContentLoaded', function () {
    const conversationDiv = document.getElementById('conversation');
    const conversationContainer = document.getElementById('conversationContainer');
    const userInput = document.getElementById('userInput');
    const sendBtn = document.getElementById('sendBtn');
    const chatInputBar = document.getElementById('chatInputBar');
    const fileInput = document.getElementById('fileInput');
    const brandIcon = document.querySelector('.navbar-brand');
    const suggestion = document.getElementById('suggestion');

    let dentistQueries = [];
    let selectedIndex = -1;

    const chatbotAjaxUrl = '/chat/chatbot_ajax';
    fetch(chatbotAjaxUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_input: '' })
    })
        .then(response => response.json())
        .then(data => {
            if (data.messages) {
                conversationDiv.innerHTML = renderMessages(data.messages);
                adjustConversationPadding();
                scrollToBottom();
            }
        })
        .catch(err => console.error('Error fetching initial data:', err));

    userInput.addEventListener('keydown', function (e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            if (suggestion.style.display === 'block' && selectedIndex >= 0) {
                const rows = suggestion.getElementsByClassName('suggestion-row');
                if (rows[selectedIndex]) {
                    userInput.value = rows[selectedIndex].getAttribute('data-query');
                    autoResize();
                    suggestion.style.display = 'none';
                    selectedIndex = -1;
                    sendMessage();
                }
            } else {
                sendMessage();
            }
        } else if (e.key === 'ArrowDown') {
            e.preventDefault();
            const rows = suggestion.getElementsByClassName('suggestion-row');
            if (suggestion.style.display === 'block' && rows.length > 0) {
                selectedIndex = (selectedIndex + 1) % rows.length;
                updateSelection(rows);
            }
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            const rows = suggestion.getElementsByClassName('suggestion-row');
            if (suggestion.style.display === 'block' && rows.length > 0) {
                selectedIndex = (selectedIndex - 1 + rows.length) % rows.length;
                updateSelection(rows);
            }
        }
    });

    userInput.addEventListener('input', function () {
        autoResize();
        adjustConversationPadding();
        showSuggestion();
    });

    sendBtn.addEventListener('click', function (e) {
        e.preventDefault();
        sendMessage();
    });

    if (brandIcon) {
        brandIcon.addEventListener('click', function (e) {
            scrollToBottom();
        });
    }

    if (fileInput) {
        fileInput.addEventListener('change', function (e) {
            const files = e.target.files;
            if (files.length > 0) {
                console.log('File selected:', files[0].name);
            }
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
                    suggestion.style.display = 'none';
                }
            })
            .catch(err => console.error('Error:', err));
    }

    function renderMessages(messages) {
        if (!messages || messages.length === 0) {
            return '<p class="fixed-message" style="font-size: 1.2rem; color: #4e4e4e;"><i>Your conversation will appear here...</i></p>';
        }

        let html = '';
        messages.forEach(msg => {
            const safeText = msg.sender === 'user' ? escapeHtml(msg.text) : decodeHtmlEntities(msg.text);

            if (msg.sender === 'user') {
                html += '<div class="chat-message user-message text-end mb-3"><div class="alert alert-secondary d-inline-block chat-bubble border-0">' + safeText + '<br></div></div>';
            } else {
                html += '<div class="chat-message bot-message d-flex align-items-start mb-3"><div class="alert alert-info d-inline-block chat-bubble mb-0 border-0 bot-bubble">' + safeText + '<br><small>' + msg.time + '</small></div></div>';
            }
        });
        return html;
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    function decodeHtmlEntities(text) {
        const textArea = document.createElement('textarea');
        textArea.innerHTML = text;
        return textArea.value;
    }

    function scrollToBottom() {
        setTimeout(() => {
            window.scrollTo(0, document.body.scrollHeight);
        }, 0);
    }

    async function showSuggestion() {
        const input = userInput.value.toLowerCase().trim();
        suggestion.style.opacity = '0';
        suggestion.style.transform = 'translateY(-100%)';

        if (input.length > 0) {
            const nlpUrl = '/nlp/api/nlp_match';
            try {
                const response = await fetch(nlpUrl, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ input: input })
                });
                const data = await response.json();
                const matchedQueries = data.matchedQueries || [];

                if (matchedQueries.length > 0) {
                    let tableHTML = '<table class="suggestion-table"><tbody>';
                    matchedQueries.forEach((query, index) => {
                        tableHTML += '<tr class="suggestion-row" data-query="' + query + '"><td class="suggestion-cell">' + query + '</td></tr>' + (index < matchedQueries.length - 1 ? '<tr><td class="separator"></td></tr>' : '');
                    });
                    tableHTML += '</tbody></table>';

                    suggestion.innerHTML = tableHTML;
                    suggestion.style.display = 'block';
                    requestAnimationFrame(() => {
                        suggestion.style.opacity = '1';
                        suggestion.style.transform = 'translateY(0)';
                    });

                    const rows = suggestion.getElementsByClassName('suggestion-row');
                    Array.from(rows).forEach(row => {
                        row.addEventListener('click', function () {
                            userInput.value = this.getAttribute('data-query');
                            autoResize();
                            suggestion.style.display = 'none';
                            selectedIndex = -1;
                        });
                    });
                } else {
                    suggestion.style.display = 'none';
                    selectedIndex = -1;
                }
            } catch (err) {
                console.error('Error fetching NLP suggestions:', err);
                suggestion.style.display = 'none';
                selectedIndex = -1;
            }
        } else {
            suggestion.style.display = 'none';
            selectedIndex = -1;
        }
    }

    function updateSelection(rows) {
        for (let i = 0; i < rows.length; i++) {
            rows[i].classList.remove('selected');
        }
        if (rows[selectedIndex]) {
            rows[selectedIndex].classList.add('selected');
            rows[selectedIndex].scrollIntoView({ block: 'nearest' });
        }
    }

    document.addEventListener('click', function (e) {
        if (!userInput.contains(e.target) && !suggestion.contains(e.target)) {
            suggestion.style.display = 'none';
            selectedIndex = -1;
        }
    });

    adjustConversationPadding();
    scrollToBottom();
});