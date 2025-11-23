// API Base URL - production veya development
const API_BASE_URL = window.location.hostname === 'localhost'
    ? 'http://localhost:8000'
    : '';

// Sayfa yüklendiğinde durumu kontrol et
window.addEventListener('DOMContentLoaded', async () => {
    await checkSystemStatus();
});

// Sistem durumunu kontrol et
async function checkSystemStatus() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/chat`);
        const data = await response.json();

        const statusDot = document.getElementById('statusDot');
        const statusText = document.getElementById('statusText');
        const chatSection = document.getElementById('chatSection');

        if (data.knowledge_base_loaded) {
            statusDot.className = 'status-dot online';
            statusText.textContent = `Sistem hazır (${data.chunks_count} parça yüklü)`;
            chatSection.style.display = 'flex';
        } else {
            statusDot.className = 'status-dot offline';
            statusText.textContent = 'Bilgi tabanı yüklenemedi';
        }
    } catch (error) {
        console.error('Durum kontrolü hatası:', error);
        const statusDot = document.getElementById('statusDot');
        const statusText = document.getElementById('statusText');
        statusDot.className = 'status-dot offline';
        statusText.textContent = 'Sunucuya bağlanılamıyor';
    }
}

// Soru gönder
async function sendQuestion() {
    const input = document.getElementById('questionInput');
    const question = input.value.trim();

    if (!question) {
        return;
    }

    // Kullanıcı mesajını ekle
    addMessage(question, 'user');
    input.value = '';
    adjustTextareaHeight(input);

    // Gönder butonunu devre dışı bırak
    const sendBtn = document.getElementById('sendBtn');
    sendBtn.disabled = true;
    sendBtn.textContent = 'Düşünüyor...';

    // Typing indicator ekle
    const typingId = addTypingIndicator();

    try {
        const response = await fetch(`${API_BASE_URL}/api/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ question: question })
        });

        if (response.ok) {
            const data = await response.json();
            removeTypingIndicator(typingId);
            addMessage(data.answer, 'bot', data.sources);
        } else {
            const error = await response.json();
            removeTypingIndicator(typingId);
            addMessage('Üzgünüm, bir hata oluştu: ' + (error.error || error.detail || 'Bilinmeyen hata'), 'bot');
        }
    } catch (error) {
        console.error('Soru gönderme hatası:', error);
        removeTypingIndicator(typingId);
        addMessage('Sunucuya bağlanırken bir hata oluştu. Lütfen tekrar deneyin.', 'bot');
    } finally {
        sendBtn.disabled = false;
        sendBtn.textContent = 'Gönder';
    }
}

// Mesaj ekle
function addMessage(text, sender, sources = null) {
    const chatMessages = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}-message`;

    let sourcesHTML = '';
    if (sources && sources.length > 0) {
        sourcesHTML = '<div class="sources"><div class="sources-title">📚 İlgili Kaynak Bölümler:</div>';
        sources.forEach((source, index) => {
            const text = typeof source === 'string' ? source : source.text;
            const page = source.page ? ` (Sayfa ${source.page})` : '';
            const preview = text.substring(0, 150) + (text.length > 150 ? '...' : '');
            sourcesHTML += `<div class="source-item">${preview}${page}</div>`;
        });
        sourcesHTML += '</div>';
    }

    messageDiv.innerHTML = `
        <div class="message-content">
            <strong>${sender === 'user' ? 'Siz' : 'Asistan'}:</strong>
            <p>${text}</p>
            ${sourcesHTML}
        </div>
    `;

    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Typing indicator ekle
function addTypingIndicator() {
    const chatMessages = document.getElementById('chatMessages');
    const typingDiv = document.createElement('div');
    const typingId = 'typing-' + Date.now();
    typingDiv.id = typingId;
    typingDiv.className = 'message bot-message';
    typingDiv.innerHTML = `
        <div class="message-content">
            <div class="typing-indicator">
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
            </div>
        </div>
    `;

    chatMessages.appendChild(typingDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;

    return typingId;
}

// Typing indicator kaldır
function removeTypingIndicator(typingId) {
    const typingDiv = document.getElementById(typingId);
    if (typingDiv) {
        typingDiv.remove();
    }
}

// Hızlı soru sor
function askQuickQuestion(question) {
    const input = document.getElementById('questionInput');
    input.value = question;
    sendQuestion();
}

// Enter tuşu ile gönder (Shift+Enter ile yeni satır)
function handleKeyPress(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        sendQuestion();
    }
}

// Textarea yüksekliğini otomatik ayarla
const textarea = document.getElementById('questionInput');
if (textarea) {
    textarea.addEventListener('input', function() {
        adjustTextareaHeight(this);
    });
}

function adjustTextareaHeight(element) {
    element.style.height = 'auto';
    element.style.height = Math.min(element.scrollHeight, 150) + 'px';
}
