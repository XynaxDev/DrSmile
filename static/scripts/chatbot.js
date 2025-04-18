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

    // Initial Setup Section
    fetch(chatbotAjaxUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_input: '' })
    })
        .then(response => response.json())
        .then(data => {
            if (data.queries) {
                dentistQueries = data.queries;
            }
        })
        .catch(err => console.error('Error fetching queries:', err));

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

    // Auto-Resize Section
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

    // Layout Adjustment Section
    function adjustConversationPadding() {
        const barHeight = chatInputBar.offsetHeight;
        conversationContainer.style.paddingBottom = barHeight + 'px';
    }

    // Message Handling Section
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
                }
            })
            .catch(err => console.error('Error:', err));
    }

    function renderMessages(messages) {
        if (!messages || messages.length === 0) {
            return '<p class="text-center" style="font-size: 1.2rem; padding-top: 50px; color: #4e4e4e;"><i>Your conversation will appear here...</i></p>';
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

    // Suggestion Handling Section
    function showSuggestion() {
        const input = userInput.value.toLowerCase().trim();
        suggestion.style.opacity = '0';
        suggestion.style.transform = 'translateY(-100%)';

        if (input) {
            const matchedQueries = dentistQueries.filter(query => query.toLowerCase().includes(input)).slice(0, 5);

            if (matchedQueries.length > 0) {
                let tableHTML = '<table class="suggestion-table"><tbody>';
                matchedQueries.forEach((query, index) => {
                    tableHTML += '<tr class="suggestion-row" data-query="' + query + '"><td class="suggestion-cell">' + query + '</td></tr>' + (index < matchedQueries.length - 1 ? '<tr><td class="separator"></td></tr>' : '');
                });
                tableHTML += '</tbody></table>';

                suggestion.innerHTML = tableHTML;
                suggestion.style.display = 'block';
                requestAnimationFrame(() => {
                    // suggestion.style.transition = 'opacity 0.4s ease-out, transform 0.4s ease-out';
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
        } else {
            suggestion.style.display = 'none';
            selectedIndex = -1;
        }
    }

    // Selection Update Section
    function updateSelection(rows) {
        for (let i = 0; i < rows.length; i++) {
            rows[i].classList.remove('selected');
        }
        if (rows[selectedIndex]) {
            rows[selectedIndex].classList.add('selected');
            rows[selectedIndex].scrollIntoView({ block: 'nearest' });
        }
    }

    // Click Handling Section
    document.addEventListener('click', function (e) {
        if (!userInput.contains(e.target) && !suggestion.contains(e.target)) {
            suggestion.style.display = 'none';
            selectedIndex = -1;
        }
    });

    adjustConversationPadding();
    scrollToBottom();
});