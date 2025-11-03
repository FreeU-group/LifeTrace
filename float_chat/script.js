// 全局变量
let chatHistory = [];
let currentStreamingMessage = null;
let settings = {
    apiUrl: 'http://127.0.0.1:8840',
    temperature: 0.7,
    maxTokens: 2000,
    systemPrompt: '你是一个有用的AI助手。',
    enableThinking: true
};

// DOM 元素
const chatMessages = document.getElementById('chatMessages');
const welcomeScreen = document.getElementById('welcomeScreen');
const messagesList = document.getElementById('messagesList');
const chatForm = document.getElementById('chatForm');
const chatInput = document.getElementById('chatInput');
const sendButton = document.getElementById('sendButton');
const settingsModal = document.getElementById('settingsModal');

// 初始化
document.addEventListener('DOMContentLoaded', function() {
    loadSettings();
    loadChatHistory();
    setupEventListeners();
    adjustInputHeight();

    // 初始化图标
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }

    // 检查是否有聊天历史
    if (chatHistory.length === 0) {
        showWelcomeScreen();
    } else {
        showChatMessages();
        renderChatHistory();
    }
});

// 设置事件监听器
function setupEventListeners() {
    console.log('Setting up event listeners...');
    console.log('chatForm:', chatForm);
    console.log('chatInput:', chatInput);
    console.log('sendButton:', sendButton);

    // 聊天表单提交 - 只使用表单的submit事件，避免重复
    if (chatForm) {
        chatForm.addEventListener('submit', handleChatSubmit);
        console.log('Form submit listener added');
    } else {
        console.error('chatForm not found!');
    }

    // 输入框自动调整高度
    if (chatInput) {
        chatInput.addEventListener('input', adjustInputHeight);

        // 快捷键支持 - 使用表单提交而不是直接调用handleChatSubmit
        chatInput.addEventListener('keydown', function(e) {
            console.log('Key pressed:', e.key, 'Shift:', e.shiftKey);
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                console.log('Enter key pressed, submitting form');
                if (chatForm) {
                    chatForm.dispatchEvent(new Event('submit'));
                }
            }
        });
        console.log('Input listeners added');
    } else {
        console.error('chatInput not found!');
    }

    // 发送按钮点击事件 - 使用表单提交而不是直接调用handleChatSubmit
    if (sendButton) {
        sendButton.addEventListener('click', function(e) {
            console.log('Send button clicked');
            e.preventDefault();
            if (chatForm) {
                chatForm.dispatchEvent(new Event('submit'));
            }
        });
        console.log('Send button listener added');
    } else {
        console.error('sendButton not found!');
    }

    // 设置模态框 - 使用onclick事件处理器，无需额外的事件监听器
    console.log('Settings modal found:', settingsModal);

    // 点击模态框外部关闭
    if (settingsModal) {
        settingsModal.addEventListener('click', function(e) {
            if (e.target === settingsModal) {
                closeSettingsModal();
            }
        });
        console.log('Settings modal click listener added');
    } else {
        console.error('settingsModal not found!');
    }

    // 快速操作按钮
    document.querySelectorAll('.quick-action').forEach(button => {
        button.addEventListener('click', function() {
            const prompt = this.textContent;
            if (chatInput) {
                chatInput.value = prompt;
                adjustInputHeight();
                chatInput.focus();
            }
        });
    });

    console.log('Event listeners setup completed');
}

// 处理聊天提交
async function handleChatSubmit(e) {
    console.log('handleChatSubmit called');
    e.preventDefault();

    if (!chatInput) {
        console.error('chatInput is null');
        return;
    }

    const message = chatInput.value.trim();
    console.log('Message to send:', message);

    if (!message) {
        console.log('No message');
        return;
    }

    console.log('Processing message submission...');

    // 清空输入框
    chatInput.value = '';
    adjustInputHeight();

    // 禁用发送按钮
    if (sendButton) {
        sendButton.disabled = true;
    }

    // 隐藏欢迎屏幕，显示聊天消息
    if (welcomeScreen && messagesList) {
        welcomeScreen.style.display = 'none';
        messagesList.style.display = 'block';
    }

    // 添加用户消息到UI与本地历史
    addMessage('user', message);
    pushHistory('user', message);

    // 滚动到最后一条用户消息，让其显示在可见区域的最上方，但留出10px空隙
    setTimeout(() => {
        const userMessages = messagesList.querySelectorAll('.message.user');
        if (userMessages.length > 0) {
            const lastUserMessage = userMessages[userMessages.length - 1];
            const chatMessagesContainer = document.querySelector('.chat-messages');
            if (chatMessagesContainer) {
                const messageRect = lastUserMessage.getBoundingClientRect();
                const containerRect = chatMessagesContainer.getBoundingClientRect();

                // 计算需要滚动的距离，留出10px空隙
                const targetScrollTop = chatMessagesContainer.scrollTop + messageRect.top - containerRect.top - 10;

                chatMessagesContainer.scrollTo({
                    top: targetScrollTop,
                    behavior: 'smooth'
                });
            }
        }
    }, 100);

    try {
        console.log('Sending request to:', settings.apiUrl);

        // 构建请求数据
        const promptWithHistory = buildPromptWithHistory(message);
        const requestData = { message: promptWithHistory };
        console.log('Request data:', requestData);

        // 显示思考状态
        if (settings.enableThinking) {
            showThinking();
        }

        // 发送请求
        const response = await fetch(`${settings.apiUrl}/api/chat/stream`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestData)
        });

        console.log('Response status:', response.status);

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        // 隐藏思考状态
        if (settings.enableThinking) {
            hideThinking();
        }

        // 创建助手消息元素
        currentStreamingMessage = addMessage('assistant', '');
        pushHistory('assistant', '');

        // 处理流式响应 - 参考chat.html的处理方式
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let fullResponse = '';

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            // 第一次接收到数据时隐藏思考指示器
            if (fullResponse === '' && settings.enableThinking) {
                hideThinking();
            }

            const chunk = decoder.decode(value, { stream: true });
            fullResponse += chunk;

            // 实时更新显示内容
            if (currentStreamingMessage) {
                // 检测并渲染Markdown
                let processedContent = fullResponse;
                if (typeof marked !== 'undefined') {
                    const hasMarkdown = /[#*`_\[\]\(\)\-\+]|\n\n/.test(fullResponse);
                    if (hasMarkdown) {
                        processedContent = marked.parse(fullResponse);
                    }
                }

                // 更新消息内容
                const messageContent = currentStreamingMessage.querySelector('.message-content');
                if (messageContent) {
                    messageContent.innerHTML = processedContent;
                }

                // 更新历史记录中的最后一条助手消息
                if (chatHistory.length > 0 && chatHistory[chatHistory.length - 1].role === 'assistant') {
                    chatHistory[chatHistory.length - 1].content = fullResponse;
                }
            }
        }

        // 流式输出结束后，重新处理截图链接
        if (currentStreamingMessage && fullResponse) {
            // 重新处理截图链接
            const processedContent = processScreenshotLinks(fullResponse);

            // 检测并渲染Markdown
            let finalContent = processedContent;
            if (typeof marked !== 'undefined') {
                const hasMarkdown = /[#*`_\[\]\(\)\-\+]|\n\n/.test(processedContent);
                if (hasMarkdown) {
                    finalContent = marked.parse(processedContent);
                }
            }

            const messageContent = currentStreamingMessage.querySelector('.message-content');
            if (messageContent) {
                messageContent.innerHTML = finalContent;
            }
        }

        // 保存聊天历史
        saveChatHistory();

    } catch (error) {
        console.error('Error in handleChatSubmit:', error);

        // 隐藏思考状态
        if (settings.enableThinking) {
            hideThinking();
        }

        // 移除可能存在的流式消息
        if (currentStreamingMessage) {
            currentStreamingMessage.remove();
            chatHistory.pop(); // 移除助手消息
        }

        let errorMessage = '抱歉，发生了错误：';
        if (error.name === 'TypeError' && error.message.includes('fetch')) {
            errorMessage += '无法连接到服务器，请检查 API 地址设置';
        } else {
            errorMessage += error.message;
        }

        // 添加错误消息
        const errorMessageElement = addMessage('assistant', errorMessage);
        errorMessageElement.querySelector('.message-card').style.background = '#fee';
        errorMessageElement.querySelector('.message-card').style.color = '#c53030';
        errorMessageElement.querySelector('.message-card').style.border = '1px solid #fed7d7';

        showNotification('发送失败，请检查网络连接和设置', 'error');

        // 保存聊天历史（包含错误消息）
        pushHistory('assistant', errorMessage);
        saveChatHistory();

        currentStreamingMessage = null;

    } finally {
        if (sendButton) {
            sendButton.disabled = false;
        }
        console.log('handleChatSubmit completed');
    }
}

// 添加消息到界面和历史
function addMessage(role, content) {
    // 隐藏欢迎屏幕，显示消息列表
    if (welcomeScreen.style.display !== 'none') {
        welcomeScreen.style.display = 'none';
        messagesList.style.display = 'flex';
    }

    // 创建消息元素
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;

    // 对于AI回复，检测并渲染Markdown
    let processedContent = content;
    if (role === 'assistant' && typeof marked !== 'undefined') {
        // 检测是否包含Markdown语法
        const hasMarkdown = /[#*`_\[\]\(\)\-\+]|\n\n/.test(content);
        if (hasMarkdown) {
            processedContent = marked.parse(content);
        }
    }

    // 处理截图ID链接（仅对AI回复）
    if (role === 'assistant') {
        processedContent = processScreenshotLinks(processedContent);
    }

    const avatarContent = role === 'user' ? 'U' : '<i data-lucide="bot"></i>';

    messageDiv.innerHTML = `
        <div class="message-avatar">${avatarContent}</div>
        <div class="message-card">
            <div class="message-content">${processedContent}</div>
        </div>
    `;

    messagesList.appendChild(messageDiv);

    // 重新创建图标
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }

    // 不再自动滚动到底部，保持用户消息居中显示
}
}

// 向消息追加内容（用于流式响应）
function appendToMessage(messageElement, content) {
    const messageContent = messageElement.querySelector('.message-content');
    const currentContent = messageContent.textContent + content;

    // 检测并渲染Markdown
    let processedContent = currentContent;
    if (typeof marked !== 'undefined') {
        const hasMarkdown = /[#*`_\[\]\(\)\-\+]|\n\n/.test(currentContent);
        if (hasMarkdown) {
            processedContent = marked.parse(currentContent);
        }
    }

    messageContent.innerHTML = processedContent;

    // 重新创建图标
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }
}

// 思考指示器相关变量
let thinkingMessageDiv = null;

// 显示思考状态
function showThinking(text = '正在思考...') {
    // 如果已经有思考指示器，先移除
    if (thinkingMessageDiv) {
        hideThinking();
    }

    // 隐藏欢迎屏幕，显示消息列表
    if (welcomeScreen.style.display !== 'none') {
        welcomeScreen.style.display = 'none';
        messagesList.style.display = 'flex';
    }

    thinkingMessageDiv = document.createElement('div');
    thinkingMessageDiv.className = 'message assistant thinking-message';

    thinkingMessageDiv.innerHTML = `
        <div class="message-avatar">
            <i data-lucide="bot"></i>
        </div>
        <div class="message-card">
            <div class="thinking-indicator">
                <div class="thinking-content">
                    <div class="thinking-text">${text}</div>
                    <div class="thinking-dots">
                        <div class="thinking-dot"></div>
                        <div class="thinking-dot"></div>
                        <div class="thinking-dot"></div>
                    </div>
                </div>
            </div>
        </div>
    `;

    // 添加到消息列表
    messagesList.appendChild(thinkingMessageDiv);

    // 使用requestAnimationFrame确保DOM更新后再添加show类
    requestAnimationFrame(() => {
        thinkingMessageDiv.classList.add('show');
    });

    // 重新创建图标
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }
}

// 隐藏思考状态
function hideThinking() {
    if (thinkingMessageDiv) {
        thinkingMessageDiv.classList.remove('show');
        // 等待动画完成后移除元素
        setTimeout(() => {
            if (thinkingMessageDiv && thinkingMessageDiv.parentNode) {
                thinkingMessageDiv.parentNode.removeChild(thinkingMessageDiv);
                thinkingMessageDiv = null;
            }
        }, 300);
    }
}

// 更新思考文本
function updateThinkingText(text) {
    if (thinkingMessageDiv) {
        const textElement = thinkingMessageDiv.querySelector('.thinking-text');
        if (textElement) {
            textElement.textContent = text;
        }
    }
}

// 滚动到底部
function scrollToBottom() {
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// 调整输入框高度
function adjustInputHeight() {
    chatInput.style.height = 'auto';
    const newHeight = Math.min(chatInput.scrollHeight, 120); // 最大高度120px
    chatInput.style.height = newHeight + 'px';
}

// 显示欢迎屏幕
function showWelcomeScreen() {
    welcomeScreen.style.display = 'flex';
    messagesList.style.display = 'none';
}

// 显示聊天消息
function showChatMessages() {
    welcomeScreen.style.display = 'none';
    messagesList.style.display = 'flex';
}

// 渲染聊天历史
function renderChatHistory() {
    messagesList.innerHTML = '';
    chatHistory.forEach(msg => {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${msg.role}`;

        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        if (msg.role === 'user') {
            avatar.textContent = 'U';
        } else {
            avatar.innerHTML = '<i data-lucide="bot"></i>';
        }

        const card = document.createElement('div');
        card.className = 'message-card';

        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';

        if (msg.role === 'assistant') {
            // 检查marked是否可用，如果不可用则使用纯文本
            if (typeof marked !== 'undefined' && marked.parse) {
                messageContent.innerHTML = marked.parse(msg.content);
            } else {
                messageContent.textContent = msg.content;
            }
        } else {
            messageContent.textContent = msg.content;
        }

        card.appendChild(messageContent);

        if (msg.role === 'user') {
            messageDiv.appendChild(card);
            messageDiv.appendChild(avatar);
        } else {
            messageDiv.appendChild(avatar);
            messageDiv.appendChild(card);
        }

        messagesList.appendChild(messageDiv);
    });

    // 重新创建图标
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }

    scrollToBottom();
}

// 加载设置
function loadSettings() {
    const savedSettings = localStorage.getItem('chatSettings');
    if (savedSettings) {
        settings = { ...settings, ...JSON.parse(savedSettings) };
    }

    // 应用主题
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'dark') {
        document.body.classList.add('dark');
    }

    // 更新设置表单
    updateSettingsForm();
}

// 更新设置表单
function updateSettingsForm() {
    const apiUrlInput = document.getElementById('api-url');
    const temperatureInput = document.getElementById('temperature');
    const temperatureValue = document.getElementById('temperature-value');
    const maxTokensInput = document.getElementById('max-tokens');
    const systemPromptInput = document.getElementById('system-prompt');
    const enableThinkingInput = document.getElementById('enable-thinking');

    if (apiUrlInput) apiUrlInput.value = settings.apiUrl;
    if (temperatureInput) {
        temperatureInput.value = settings.temperature;
        if (temperatureValue) temperatureValue.textContent = settings.temperature;
    }
    if (maxTokensInput) maxTokensInput.value = settings.maxTokens;
    if (systemPromptInput) systemPromptInput.value = settings.systemPrompt;
    if (enableThinkingInput) enableThinkingInput.checked = settings.enableThinking;
}

// 处理保存设置
function handleSaveSettings() {
    settings.apiUrl = document.getElementById('api-url').value;
    settings.temperature = parseFloat(document.getElementById('temperature').value);
    settings.maxTokens = parseInt(document.getElementById('max-tokens').value);
    settings.systemPrompt = document.getElementById('system-prompt').value;
    settings.enableThinking = document.getElementById('enable-thinking').checked;

    localStorage.setItem('chatSettings', JSON.stringify(settings));
    settingsModal.style.display = 'none';

    // 显示保存成功提示
    showNotification('设置已保存');
}

// 显示通知
function showNotification(message) {
    // 创建通知元素
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: var(--primary);
        color: var(--primary-foreground);
        padding: 12px 20px;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        z-index: 1001;
        animation: slideInRight 0.3s ease-out;
    `;
    notification.textContent = message;

    document.body.appendChild(notification);

    // 3秒后自动移除
    setTimeout(() => {
        notification.style.animation = 'slideOutRight 0.3s ease-out';
        setTimeout(() => {
            document.body.removeChild(notification);
        }, 300);
    }, 3000);
}

// 加载聊天历史
function loadChatHistory() {
    const saved = localStorage.getItem('chatHistory');
    if (saved) {
        chatHistory = JSON.parse(saved);
    }
}

// 保存聊天历史
function saveChatHistory() {
    localStorage.setItem('chatHistory', JSON.stringify(chatHistory));
}

// 构建带有历史的提示
function buildPromptWithHistory(message, maxHistory = 6) {
    // 获取最近的历史记录（不包括当前消息）
    const recentHistory = chatHistory.slice(-maxHistory);

    // 如果没有历史记录，直接返回当前消息
    if (recentHistory.length === 0) {
        return message;
    }

    // 构建包含历史的提示
    let prompt = '';
    for (const item of recentHistory) {
        if (item.role === 'user') {
            prompt += `用户: ${item.content}\n`;
        } else if (item.role === 'assistant') {
            prompt += `助手: ${item.content}\n`;
        }
    }

    // 添加当前消息
    prompt += `用户: ${message}`;

    return prompt;
}

// 处理截图链接
function processScreenshotLinks(content) {
    // 处理截图ID范围 (例如: screenshot:1-5)
    content = content.replace(/screenshot:(\d+)-(\d+)/g, (match, start, end) => {
        const startNum = parseInt(start);
        const endNum = parseInt(end);
        let html = '';
        for (let i = startNum; i <= endNum; i++) {
            html += `<span class="screenshot-link" onclick="showScreenshotPreview(${i})">📷 截图${i}</span> `;
        }
        return html.trim();
    });

    // 处理单个截图ID (例如: screenshot:3)
    content = content.replace(/screenshot:(\d+)/g, (match, id) => {
        return `<span class="screenshot-link" onclick="showScreenshotPreview(${id})">📷 截图${id}</span>`;
    });

    // 处理多个截图ID (例如: screenshot:1,3,5)
    content = content.replace(/screenshot:([\d,]+)/g, (match, ids) => {
        const idList = ids.split(',');
        let html = '';
        for (const id of idList) {
            const trimmedId = id.trim();
            if (trimmedId) {
                html += `<span class="screenshot-link" onclick="showScreenshotPreview(${trimmedId})">📷 截图${trimmedId}</span> `;
            }
        }
        return html.trim();
    });

    return content;
}

// 推送消息到历史记录
function pushHistory(role, content) {
    chatHistory.push({ role, content });
    saveChatHistory();
}

// 显示截图预览（占位函数）
function showScreenshotPreview(id) {
    console.log('显示截图预览:', id);
    // 这里可以添加截图预览的具体实现
}

// 添加通知动画样式
const style = document.createElement('style');
style.textContent = `
    @keyframes slideInRight {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }

    @keyframes slideOutRight {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

// 添加缺失的函数
function insertQuickQuery(query) {
    const chatInput = document.getElementById('chatInput');
    if (chatInput) {
        chatInput.value = query;
        adjustInputHeight();
        chatInput.focus();
    }
}

function closeSettingsModal() {
    const settingsModal = document.getElementById('settingsModal');
    if (settingsModal) {
        settingsModal.style.display = 'none';
    }
}

function saveSettings() {
    const localHistoryEnabled = document.getElementById('localHistoryEnabled');
    const historyLimit = document.getElementById('historyLimit');
    const serverUrl = document.getElementById('serverUrl');

    if (localHistoryEnabled) {
        settings.localHistoryEnabled = localHistoryEnabled.checked;
    }
    if (historyLimit) {
        settings.historyLimit = parseInt(historyLimit.value) || 6;
    }
    if (serverUrl) {
        settings.apiUrl = serverUrl.value || 'http://localhost:8000';
    }

    // 保存到本地存储
    if (typeof Storage !== 'undefined') {
        localStorage.setItem('lifetrace_settings', JSON.stringify(settings));
    }

    closeSettingsModal();
    showNotification('设置已保存');
}

function clearAllHistory() {
    if (confirm('确定要清除所有历史记录吗？此操作不可撤销。')) {
        chatHistory = [];
        if (typeof Storage !== 'undefined') {
            localStorage.removeItem('lifetrace_chat_history');
        }

        // 清空UI
        const messagesList = document.getElementById('messagesList');
        if (messagesList) {
            messagesList.innerHTML = '';
        }

        showWelcomeScreen();
        showNotification('历史记录已清除');
    }
}

// Electron API 集成
if (window.electronAPI) {
    // 获取版本信息
    window.electronAPI.getVersion().then(version => {
        console.log('Electron version:', version);
    });
}
