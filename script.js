document.addEventListener('DOMContentLoaded', () => {
    // --- DOM Element Selectors ---
    const chatIcon = document.querySelector('.chat-icon-button');
    const chatWidget = document.querySelector('.chat-widget');
    const closeBtn = document.querySelector('.close-btn');
    const chatBody = document.querySelector('.chat-body');
    const inputField = document.querySelector('.chat-input-box input');
    const sendBtn = document.querySelector('.chat-input-box button');
    const quickActionsContainer = document.querySelector('.quick-actions-container');

    if (!chatIcon || !chatWidget || !closeBtn || !chatBody || !inputField || !sendBtn) {
        console.error("One or more chat elements could not be found in the DOM.");
        return;
    }

    const API_URL = 'https://elgiganten-7k17.onrender.com/chat';
    let isFirstOpen = true;

    // --- Event Listeners ---
    chatIcon.addEventListener('click', toggleChatWidget);
    closeBtn.addEventListener('click', toggleChatWidget);
    sendBtn.addEventListener('click', handleUserMessage);
    inputField.addEventListener('keydown', (event) => {
        if (event.key === 'Enter') {
            handleUserMessage();
        }
    });

    // --- Core Functions ---

    function toggleChatWidget() {
        chatWidget.classList.toggle('open');
        if (chatWidget.classList.contains('open') && isFirstOpen) {
            isFirstOpen = false;
            showWelcomeMessage();
        }
    }

    function showWelcomeMessage() {
        setTimeout(() => {
            const greeting = "Hello! I'm V, your virtual guide. How can I help you today?";
            addBotMessage(greeting);
            addQuickActionButtons();
        }, 1500);
    }

    function addQuickActionButtons() {
        quickActionsContainer.innerHTML = '';
        const actions = ['Return', 'Connect to human agent', 'Other questions'];
        const actionsWrapper = document.createElement('div');
        actionsWrapper.className = 'quick-actions';
        actions.forEach(actionText => {
            const button = document.createElement('button');
            button.className = 'quick-action-btn';
            button.textContent = actionText;
            button.addEventListener('click', () => {
                sendQuery(actionText);
                quickActionsContainer.innerHTML = '';
            });
            actionsWrapper.appendChild(button);
        });
        quickActionsContainer.appendChild(actionsWrapper);
        scrollToBottom();
    }

    function handleUserMessage() {
        const query = inputField.value.trim();
        if (!query) return;
        sendQuery(query);
        inputField.value = '';
    }

    async function sendQuery(query) {
        addUserMessage(query);
        showTypingIndicator();
        try {
            const response = await fetch(API_URL, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query: query }),
            });
            if (!response.ok) throw new Error(`Error: ${response.statusText}`);
            const data = await response.json();
            addBotMessage(data.response);
        } catch (error) {
            console.error("Failed to get response from backend:", error);
            addBotMessage("Sorry, I'm having trouble connecting. Please try again later.");
        }
    }

    function addUserMessage(message) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message user-message';
        messageDiv.textContent = message;
        chatBody.insertBefore(messageDiv, quickActionsContainer);
        addTimestamp(messageDiv);
        scrollToBottom();
    }

    /**
     * UPDATED to handle product cards
     * @param {string|object} response - The bot's response.
     */
    function addBotMessage(response) {
        const typingIndicator = chatBody.querySelector('.typing-indicator');
        if (typingIndicator) typingIndicator.parentElement.remove();

        // Handle text part of the response
        if (response && response.text) {
            const messageDiv = document.createElement('div');
            messageDiv.className = 'message bot-message';
            messageDiv.textContent = response.text;
            chatBody.insertBefore(messageDiv, quickActionsContainer);
            addTimestamp(messageDiv);
        }

        // Handle products part of the response
        if (response && response.products && response.products.length > 0) {
            response.products.forEach(product => {
                const card = createProductCard(product);
                chatBody.insertBefore(card, quickActionsContainer);
            });
        }

        // Fallback for simple string responses or other objects
        if (typeof response === 'string') {
            const messageDiv = document.createElement('div');
            messageDiv.className = 'message bot-message';
            messageDiv.textContent = response;
            chatBody.insertBefore(messageDiv, quickActionsContainer);
            addTimestamp(messageDiv);
        }

        scrollToBottom();
    }

    /**
     * Creates an HTML element for a product card.
     * @param {object} product - The product data from the backend.
     * @returns {HTMLElement} - The product card element.
     */
    function createProductCard(product) {
        const cardLink = document.createElement('a');
        cardLink.className = 'product-card';
        cardLink.href = product.product_url;
        cardLink.target = '_blank'; // Open in a new tab
        cardLink.rel = 'noopener noreferrer';

        const productImage = document.createElement('img');
        productImage.src = product.image_url;
        productImage.alt = product.title;

        const productTitle = document.createElement('div');
        productTitle.className = 'product-title';
        productTitle.textContent = product.title;

        cardLink.appendChild(productImage);
        cardLink.appendChild(productTitle);

        return cardLink;
    }

    function showTypingIndicator() {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message bot-message';
        const indicatorDiv = document.createElement('div');
        indicatorDiv.className = 'typing-indicator';
        indicatorDiv.innerHTML = '<span></span><span></span><span></span>';
        messageDiv.appendChild(indicatorDiv);
        chatBody.insertBefore(messageDiv, quickActionsContainer);
        scrollToBottom();
    }

    function addTimestamp(messageElement) {
        const timestampDiv = document.createElement('div');
        timestampDiv.className = 'timestamp';
        timestampDiv.textContent = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        messageElement.insertAdjacentElement('afterend', timestampDiv);
    }

    function scrollToBottom() {
        chatBody.scrollTop = chatBody.scrollHeight;
    }
});