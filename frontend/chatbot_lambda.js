const API_URL = 'https://a2emnug7k3.execute-api.eu-west-1.amazonaws.com'

document.addEventListener("DOMContentLoaded", function () {
    startChatbot();
});

function startChatbot() {
    const chatToggle = document.getElementById('chat-toggle');
    const chatWidget = document.getElementById('chat-widget');
    const chatClose = document.getElementById('chat-close');
    const chatForm = document.getElementById('chat-form');
    const chatInput = document.getElementById('chat-input');
    const chatMessages = document.getElementById('chat-messages');
    
    addBotMessage('Cześć! 👋 Jestem asystentem sklepu. Jak mogę Ci pomóc?');
 
    chatToggle.addEventListener('click', function() {
        openChat();
    });

    chatClose.addEventListener('click', function() {
        closeChat();
    });
    
    function openChat() {
        chatWidget.classList.add('open');
        chatToggle.classList.add('hidden');
        chatInput.focus(); 
    }
    
    function closeChat() {
        chatWidget.classList.remove('open');
        chatToggle.classList.remove('hidden');
    }


    chatForm.addEventListener('submit', function(e) {
        e.preventDefault(); 
        sendMessage();
    });
    
    function sendMessage() {
        const message = chatInput.value.trim();
        
        if (message === '') {
            return; 
        }
        
        addUserMessage(message);
        
        chatInput.value = '';

        showTyping();

        sendToLambda(message);
    }
    
    
    async function sendToLambda(message) {
        try {
            const response = await fetch(API_URL, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ message: message })
            });
            
            const data = await response.json();
            
            hideTyping();
            
            if (data.response) {
                addBotMessage(data.response);
            } else {
                addBotMessage('Przepraszam, wystąpił błąd. Spróbuj ponownie.');
            }
            
        } catch (error) {
            hideTyping();
            addBotMessage('Przepraszam, nie mogę się połączyć z serwerem.');
            console.log('Błąd:', error);
        }
    }

    function addUserMessage(text) {
        const messageDiv = document.createElement('div')
        messageDiv.className = 'message user-message';

        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        contentDiv.textContent = text;

        messageDiv.appendChild(contentDiv);

        chatMessages.appendChild(messageDiv);

        scrollDown();
    }

    function addBotMessage(text) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message assistant-message';

        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        contentDiv.textContent = text

        messageDiv.appendChild(contentDiv);

        chatMessages.appendChild(messageDiv);

        scrollDown()
    }

    function showTyping() {
        const typingDiv = document.createElement('div');
        typingDiv.id = 'typing-indicator';
        typingDiv.className = 'message assistant-message'

        const dotsDiv = document.createElement('div');
        dotsDiv.className = 'typing-indicator';
        dotsDiv.innerHtml = '<span></span><span></span><span></span>';

        typingDiv.appendChild(dotsDiv);
        chatMessages.appendChild(typingDiv)

        scrollDown();
    }

    function hideTyping() {
        const typingIndicator = document.getElementById('typing-indicator');
        if (typingIndicator) {
            typingIndicator.remove()
        }
    }

    function scrollDown() {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
}