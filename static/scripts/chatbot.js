document.addEventListener('DOMContentLoaded', function () {
    const conversationDiv = document.getElementById('conversation');
    const conversationContainer = document.getElementById('conversationContainer');
    const userInput = document.getElementById('userInput');
    const sendBtn = document.getElementById('sendBtn');
    const chatInputBar = document.getElementById('chatInputBar');
    const fileInput = document.getElementById('fileInput');
    const brandIcon = document.querySelector('.navbar-brand');
    const suggestion = document.getElementById('suggestion');

    let dentistQueries = []; // Will be populated from server

    // Fetch queries from server on page load
    fetch(chatbotAjaxUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_input: '' }) // Empty input to get queries
    })
        .then(response => response.json())
        .then(data => {
            if (data.queries) {
                dentistQueries = data.queries;
            } else {
                console.error('No queries found in response:', data);
            }
        })
        .catch(err => console.error('Error fetching queries:', err));

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
        showSuggestion(); // Call suggestion function on input
    });

    // Send message on click of send icon
    sendBtn.addEventListener('click', function (e) {
        e.preventDefault();
        sendMessage();
    });

    // Scroll to bottom when the brand icon is clicked
    if (brandIcon) {
        brandIcon.addEventListener('click', function (e) {
            scrollToBottom();
        });
    }

    // Handle file input (placeholder for future implementation)
    if (fileInput) {
        fileInput.addEventListener('change', function (e) {
            const files = e.target.files;
            if (files.length > 0) {
                console.log('File selected:', files[0].name);
                // Future implementation: Upload file to server and display in chat
            }
        });
    }

    function autoResize() {
        userInput.style.height = '55px';
        let neededHeight = userInput.scrollHeight;
        if (neededHeight > 150) {
            neededHeight = 150;
            userInput.style.overflowY = 'auto'; /* Scrollbar appears */
        } else {
            userInput.style.overflowY = 'hidden'; /* Scrollbar hidden, but styles still apply */
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
            const safeText = msg.sender === 'user'
                ? escapeHtml(msg.text)
                : decodeHtmlEntities(msg.text); // Use decodeHtmlEntities for bot messages

            if (msg.sender === 'user') {
                html += `
                <div class="chat-message user-message text-end mb-3">
                    <div class="alert alert-secondary d-inline-block chat-bubble border-0">
                        ${safeText}<br>
                    </div>
                </div>`;
            } else {
                html += `
                <div class="chat-message bot-message d-flex align-items-start mb-3">
                    <div class="alert alert-info d-inline-block chat-bubble mb-0 border-0 bot-bubble">
                        ${safeText}<br>
                        <small>${msg.time}</small>
                    </div>
                </div>`;
            }
        });
        return html;
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // Enhanced function to decode a broader range of HTML entities
    function decodeHtmlEntities(text) {
        const textArea = document.createElement('textarea');
        textArea.innerHTML = text;
        return textArea.value;
        // Fallback with he library (optional, uncomment if needed)
        // if (typeof he !== 'undefined') {
        //     return he.decode(text);
        // }
        // return textArea.value;
    }

    function scrollToBottom() {
        setTimeout(() => {
            window.scrollTo(0, document.body.scrollHeight);
        }, 0);
    }

    // Function to show up to 5 animated suggestions in a table
    function showSuggestion() {
        const input = userInput.value.toLowerCase().trim();
        suggestion.style.opacity = '0'; // Start with hidden state for animation
        suggestion.style.transform = 'translateY(-10px)'; // Start slightly above

        if (input) {
            const matchedQueries = dentistQueries
                .filter(query => query.toLowerCase().includes(input))
                .slice(0, 5); // Limit to 5 suggestions

            if (matchedQueries.length > 0) {
                // Create table structure
                let tableHTML = '<table class="suggestion-table"><tbody>';
                matchedQueries.forEach((query, index) => {
                    tableHTML += `
                        <tr class="suggestion-row" data-query="${query}">
                            <td class="suggestion-cell">${query}</td>
                        </tr>
                        ${index < matchedQueries.length - 1 ? '<tr><td class="separator"></td></tr>' : ''}
                    `;
                });
                tableHTML += '</tbody></table>';

                suggestion.innerHTML = tableHTML;
                suggestion.style.display = 'block';
                // Animate in
                requestAnimationFrame(() => {
                    suggestion.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
                    suggestion.style.opacity = '1';
                    suggestion.style.transform = 'translateY(0)';
                });

                // Add click event to each row
                const rows = suggestion.getElementsByClassName('suggestion-row');
                Array.from(rows).forEach(row => {
                    row.addEventListener('click', function () {
                        userInput.value = this.getAttribute('data-query');
                        autoResize(); // Adjust textarea height
                        suggestion.style.display = 'none'; // Hide after selection
                    });
                });
            } else {
                suggestion.style.display = 'none';
            }
        } else {
            suggestion.style.display = 'none';
        }
    }

    // Hide suggestion when clicking outside
    document.addEventListener('click', function (e) {
        if (!userInput.contains(e.target) && !suggestion.contains(e.target)) {
            suggestion.style.display = 'none';
        }
    });

    adjustConversationPadding();
    scrollToBottom();
});