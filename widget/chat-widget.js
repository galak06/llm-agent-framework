(function () {
  'use strict';

  const WIDGET_ID = 'llm-chat-widget';
  const script = document.currentScript;

  // --- Config from data attributes ---
  const CONFIG = {
    apiUrl: script?.getAttribute('data-api-url') || '',
    apiKey: script?.getAttribute('data-api-key') || '',
    position: script?.getAttribute('data-position') || 'right',
    title: script?.getAttribute('data-title') || 'Assistant',
    subtitle: script?.getAttribute('data-subtitle') || 'Online',
    welcome: script?.getAttribute('data-welcome') || 'Hi! How can I help you?',
    placeholder: script?.getAttribute('data-placeholder') || 'Type a message...',
    footerText: script?.getAttribute('data-footer-text') || '',
    footerUrl: script?.getAttribute('data-footer-url') || '',
    primaryColor: script?.getAttribute('data-primary-color') || '#4f46e5',
    icon: script?.getAttribute('data-icon') || 'chat',
    quickActions: script?.getAttribute('data-quick-actions') || '',
  };

  const POLL_INTERVAL = 1000;
  const MAX_POLLS = 60;

  // --- State ---
  let isOpen = false;
  let isLoading = false;
  let sessionId = `sess_${crypto.randomUUID()}`;

  // --- Color helpers ---
  function hexToRgb(hex) {
    const r = parseInt(hex.slice(1, 3), 16);
    const g = parseInt(hex.slice(3, 5), 16);
    const b = parseInt(hex.slice(5, 7), 16);
    return `${r}, ${g}, ${b}`;
  }

  function darken(hex, amount) {
    const num = parseInt(hex.slice(1), 16);
    const r = Math.max(0, (num >> 16) - amount);
    const g = Math.max(0, ((num >> 8) & 0x00ff) - amount);
    const b = Math.max(0, (num & 0x0000ff) - amount);
    return `#${(1 << 24 | r << 16 | g << 8 | b).toString(16).slice(1)}`;
  }

  const rgb = hexToRgb(CONFIG.primaryColor);

  // --- Styles ---
  const styles = `
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');

    #${WIDGET_ID} {
      --cw-primary: ${CONFIG.primaryColor};
      --cw-primary-hover: ${darken(CONFIG.primaryColor, 20)};
      --cw-primary-light: ${CONFIG.primaryColor}12;
      --cw-primary-rgb: ${rgb};
      --cw-bg: #ffffff;
      --cw-bg-chat: #f8fafc;
      --cw-text: #1e293b;
      --cw-text-light: #64748b;
      --cw-border: #e2e8f0;
      --cw-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
      --cw-radius: 16px;
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
      position: fixed;
      bottom: 24px;
      ${CONFIG.position === 'left' ? 'left: 24px;' : 'right: 24px;'}
      z-index: 999999;
      line-height: 1.5;
      font-size: 14px;
      box-sizing: border-box;
    }

    #${WIDGET_ID} *, #${WIDGET_ID} *::before, #${WIDGET_ID} *::after {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }

    .cw-toggle {
      width: 64px;
      height: 64px;
      border-radius: 50%;
      border: none;
      background: var(--cw-primary);
      color: white;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      box-shadow: 0 4px 20px rgba(var(--cw-primary-rgb), 0.4);
      transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
      position: relative;
      overflow: hidden;
    }

    .cw-toggle:hover {
      transform: scale(1.08);
      box-shadow: 0 6px 28px rgba(var(--cw-primary-rgb), 0.5);
    }

    .cw-toggle:active { transform: scale(0.95); }

    .cw-toggle svg { width: 28px; height: 28px; transition: all 0.3s ease; }

    .cw-toggle .cw-icon-close {
      position: absolute;
      opacity: 0;
      transform: rotate(-90deg) scale(0.5);
    }

    .cw-toggle.cw-open .cw-icon-main {
      opacity: 0;
      transform: rotate(90deg) scale(0.5);
    }

    .cw-toggle.cw-open .cw-icon-close {
      opacity: 1;
      transform: rotate(0) scale(1);
    }

    .cw-toggle .cw-pulse {
      position: absolute;
      width: 100%;
      height: 100%;
      border-radius: 50%;
      background: var(--cw-primary);
      animation: cw-pulse 2s ease-in-out infinite;
      z-index: -1;
    }

    @keyframes cw-pulse {
      0%, 100% { transform: scale(1); opacity: 0.4; }
      50% { transform: scale(1.2); opacity: 0; }
    }

    .cw-window {
      position: absolute;
      bottom: 80px;
      ${CONFIG.position === 'left' ? 'left: 0;' : 'right: 0;'}
      width: 400px;
      max-width: calc(100vw - 48px);
      height: 560px;
      max-height: calc(100vh - 140px);
      background: var(--cw-bg);
      border-radius: var(--cw-radius);
      box-shadow: var(--cw-shadow);
      display: flex;
      flex-direction: column;
      overflow: hidden;
      opacity: 0;
      transform: translateY(20px) scale(0.95);
      pointer-events: none;
      transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1);
      border: 1px solid var(--cw-border);
    }

    .cw-window.cw-visible {
      opacity: 1;
      transform: translateY(0) scale(1);
      pointer-events: all;
    }

    .cw-header {
      background: linear-gradient(135deg, var(--cw-primary) 0%, ${darken(CONFIG.primaryColor, -30)} 100%);
      color: white;
      padding: 20px;
      display: flex;
      align-items: center;
      gap: 12px;
      flex-shrink: 0;
    }

    .cw-avatar {
      width: 44px;
      height: 44px;
      border-radius: 50%;
      background: rgba(255, 255, 255, 0.2);
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
      overflow: hidden;
    }

    .cw-avatar svg { width: 24px; height: 24px; }
    .cw-avatar img { width: 100%; height: 100%; object-fit: cover; }

    .cw-header-text h3 { font-size: 16px; font-weight: 600; margin: 0; }

    .cw-header-text p { font-size: 12px; opacity: 0.85; margin: 2px 0 0; }

    .cw-status-dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: #4ade80;
      display: inline-block;
      margin-right: 4px;
      animation: cw-glow 2s ease-in-out infinite;
    }

    @keyframes cw-glow {
      0%, 100% { box-shadow: 0 0 4px rgba(74, 222, 128, 0.4); }
      50% { box-shadow: 0 0 8px rgba(74, 222, 128, 0.8); }
    }

    .cw-messages {
      flex: 1;
      overflow-y: auto;
      padding: 16px;
      background: var(--cw-bg-chat);
      display: flex;
      flex-direction: column;
      gap: 12px;
      scroll-behavior: smooth;
    }

    .cw-messages::-webkit-scrollbar { width: 5px; }
    .cw-messages::-webkit-scrollbar-track { background: transparent; }
    .cw-messages::-webkit-scrollbar-thumb { background: var(--cw-border); border-radius: 10px; }

    .cw-msg {
      max-width: 85%;
      padding: 10px 14px;
      border-radius: 14px;
      font-size: 14px;
      line-height: 1.5;
      animation: cw-fade-in 0.3s ease;
      word-wrap: break-word;
      overflow-wrap: anywhere;
      word-break: break-word;
      white-space: pre-wrap;
      overflow: hidden;
    }

    @keyframes cw-fade-in {
      from { opacity: 0; transform: translateY(8px); }
      to { opacity: 1; transform: translateY(0); }
    }

    .cw-msg-user {
      align-self: flex-end;
      background: var(--cw-primary);
      color: white;
      border-bottom-right-radius: 4px;
    }

    .cw-msg-bot {
      align-self: flex-start;
      background: white;
      color: var(--cw-text);
      border: 1px solid var(--cw-border);
      border-bottom-left-radius: 4px;
    }

    .cw-msg-welcome {
      align-self: center;
      background: var(--cw-primary-light);
      color: var(--cw-primary);
      border-radius: 12px;
      text-align: center;
      font-size: 13px;
      max-width: 100%;
      padding: 12px 16px;
      white-space: normal;
    }

    .cw-typing {
      align-self: flex-start;
      display: flex;
      gap: 4px;
      padding: 12px 16px;
      background: white;
      border: 1px solid var(--cw-border);
      border-radius: 14px;
      border-bottom-left-radius: 4px;
    }

    .cw-typing span {
      width: 7px;
      height: 7px;
      border-radius: 50%;
      background: var(--cw-text-light);
      animation: cw-bounce 1.4s ease-in-out infinite;
    }

    .cw-typing span:nth-child(2) { animation-delay: 0.2s; }
    .cw-typing span:nth-child(3) { animation-delay: 0.4s; }

    @keyframes cw-bounce {
      0%, 60%, 100% { transform: translateY(0); opacity: 0.4; }
      30% { transform: translateY(-6px); opacity: 1; }
    }

    .cw-quick-actions {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      padding: 0 16px 12px;
      background: var(--cw-bg-chat);
    }

    .cw-quick-btn {
      padding: 6px 12px;
      border-radius: 20px;
      border: 1px solid var(--cw-border);
      background: white;
      color: var(--cw-text);
      font-size: 12px;
      cursor: pointer;
      transition: all 0.2s;
      font-family: inherit;
    }

    .cw-quick-btn:hover {
      border-color: var(--cw-primary);
      color: var(--cw-primary);
      background: var(--cw-primary-light);
    }

    .cw-input-area {
      padding: 12px 16px;
      border-top: 1px solid var(--cw-border);
      display: flex;
      gap: 8px;
      align-items: flex-end;
      background: var(--cw-bg);
      flex-shrink: 0;
    }

    .cw-input {
      flex: 1;
      border: 1px solid var(--cw-border);
      border-radius: 12px;
      padding: 10px 14px;
      font-size: 14px;
      font-family: inherit;
      outline: none;
      resize: none;
      max-height: 80px;
      line-height: 1.4;
      transition: border-color 0.2s;
      color: var(--cw-text);
      background: var(--cw-bg-chat);
    }

    .cw-input::placeholder { color: var(--cw-text-light); }
    .cw-input:focus { border-color: var(--cw-primary); }

    .cw-send {
      width: 40px;
      height: 40px;
      border-radius: 10px;
      border: none;
      background: var(--cw-primary);
      color: white;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: all 0.2s;
      flex-shrink: 0;
    }

    .cw-send:hover:not(:disabled) { background: var(--cw-primary-hover); }
    .cw-send:disabled { opacity: 0.5; cursor: not-allowed; }
    .cw-send svg { width: 18px; height: 18px; }

    .cw-footer {
      text-align: center;
      padding: 8px;
      font-size: 11px;
      color: var(--cw-text-light);
      background: var(--cw-bg);
      border-top: 1px solid var(--cw-border);
      flex-shrink: 0;
    }

    .cw-footer a { color: var(--cw-primary); text-decoration: none; }

    @media (max-width: 480px) {
      .cw-window {
        width: calc(100vw - 16px);
        height: calc(100vh - 100px);
        bottom: 76px;
        ${CONFIG.position === 'left' ? 'left: -16px;' : 'right: -16px;'}
        border-radius: 12px;
      }
      .cw-toggle { width: 56px; height: 56px; }
    }
  `;

  // --- Icons ---
  const ICONS = {
    chat: '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2z"/></svg>',
    paw: '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M8.35 3c1.18-.17 2.43 1.12 2.79 2.9.36 1.77-.29 3.35-1.47 3.53-1.17.18-2.43-1.11-2.8-2.89-.37-1.77.3-3.36 1.48-3.54zm7.15 0c1.18.18 1.85 1.77 1.48 3.54-.37 1.78-1.63 3.07-2.8 2.89-1.18-.18-1.83-1.76-1.47-3.53.36-1.78 1.61-3.07 2.79-2.9zM3.05 10.13c1.07-.63 2.62.05 3.46 1.52.84 1.47.68 3.13-.39 3.76-1.07.63-2.62-.06-3.46-1.53-.84-1.47-.68-3.12.39-3.75zm17.9 0c1.07.63 1.23 2.28.39 3.75-.84 1.47-2.39 2.16-3.46 1.53-1.07-.63-1.23-2.29-.39-3.76.84-1.47 2.39-2.15 3.46-1.52zM12 13.5c2.76 0 5 1.79 5 4 0 2.21-2.24 4-5 4s-5-1.79-5-4c0-2.21 2.24-4 5-4z"/></svg>',
    bot: '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 2a2 2 0 0 1 2 2c0 .74-.4 1.39-1 1.73V7h1a7 7 0 0 1 7 7h1a1 1 0 0 1 1 1v3a1 1 0 0 1-1 1h-1v1a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2v-1H3a1 1 0 0 1-1-1v-3a1 1 0 0 1 1-1h1a7 7 0 0 1 7-7h1V5.73A2 2 0 0 1 12 2zM9.5 13a1.5 1.5 0 1 0 0 3 1.5 1.5 0 0 0 0-3zm5 0a1.5 1.5 0 1 0 0 3 1.5 1.5 0 0 0 0-3z"/></svg>',
  };
  const closeIcon = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>';
  const sendIcon = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>';

  function getMainIcon() {
    if (CONFIG.icon.startsWith('http') || CONFIG.icon.startsWith('/')) {
      return `<img src="${CONFIG.icon}" alt="">`;
    }
    return ICONS[CONFIG.icon] || ICONS.chat;
  }

  function getAvatarContent() {
    if (CONFIG.icon.startsWith('http') || CONFIG.icon.startsWith('/')) {
      return `<img src="${CONFIG.icon}" alt="">`;
    }
    return ICONS[CONFIG.icon] || ICONS.chat;
  }

  // --- Quick actions ---
  function buildQuickActions() {
    if (!CONFIG.quickActions) return '';
    const actions = CONFIG.quickActions.split('|').map((a) => a.trim()).filter(Boolean);
    if (!actions.length) return '';
    return `<div class="cw-quick-actions" id="cw-quick-actions">${actions
      .map((a) => `<button class="cw-quick-btn" data-msg="${a}">${a}</button>`)
      .join('')}</div>`;
  }

  // --- Footer ---
  function buildFooter() {
    if (!CONFIG.footerText) return '';
    const link = CONFIG.footerUrl
      ? `<a href="${CONFIG.footerUrl}" target="_blank">${CONFIG.footerText}</a>`
      : CONFIG.footerText;
    return `<div class="cw-footer">Powered by ${link}</div>`;
  }

  // --- Text cleanup ---
  function stripMarkdown(text) {
    return text
      .replace(/#{1,6}\s+/g, '')
      .replace(/\*\*(.+?)\*\*/g, '$1')
      .replace(/\*(.+?)\*/g, '$1')
      .replace(/__(.+?)__/g, '$1')
      .replace(/_(.+?)_/g, '$1')
      .replace(/`(.+?)`/g, '$1')
      .replace(/^\s*[-*+]\s+/gm, '- ')
      .replace(/^\s*\d+\.\s+/gm, '')
      .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
      .replace(/\n{3,}/g, '\n\n')
      .trim();
  }

  // --- Build DOM ---
  function createWidget() {
    const container = document.createElement('div');
    container.id = WIDGET_ID;

    const styleEl = document.createElement('style');
    styleEl.textContent = styles;
    container.appendChild(styleEl);

    container.innerHTML += `
      <div class="cw-window" id="cw-window">
        <div class="cw-header">
          <div class="cw-avatar">${getAvatarContent()}</div>
          <div class="cw-header-text">
            <h3>${CONFIG.title}</h3>
            <p><span class="cw-status-dot"></span>${CONFIG.subtitle}</p>
          </div>
        </div>
        <div class="cw-messages" id="cw-messages">
          <div class="cw-msg cw-msg-welcome">${CONFIG.welcome}</div>
        </div>
        ${buildQuickActions()}
        <div class="cw-input-area">
          <textarea class="cw-input" id="cw-input" placeholder="${CONFIG.placeholder}" rows="1"></textarea>
          <button class="cw-send" id="cw-send" disabled>${sendIcon}</button>
        </div>
        ${buildFooter()}
      </div>
      <button class="cw-toggle" id="cw-toggle">
        <span class="cw-pulse"></span>
        <span class="cw-icon-main">${getMainIcon()}</span>
        <span class="cw-icon-close">${closeIcon}</span>
      </button>
    `;

    document.body.appendChild(container);
    bindEvents();
  }

  // --- Events ---
  function bindEvents() {
    const toggle = document.getElementById('cw-toggle');
    const input = document.getElementById('cw-input');
    const send = document.getElementById('cw-send');
    const quickActions = document.getElementById('cw-quick-actions');

    toggle.addEventListener('click', toggleWindow);

    input.addEventListener('input', () => {
      send.disabled = !input.value.trim() || isLoading;
      input.style.height = 'auto';
      input.style.height = Math.min(input.scrollHeight, 80) + 'px';
    });

    input.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        if (input.value.trim() && !isLoading) sendMessage();
      }
    });

    send.addEventListener('click', () => {
      if (input.value.trim() && !isLoading) sendMessage();
    });

    if (quickActions) {
      quickActions.addEventListener('click', (e) => {
        const btn = e.target.closest('.cw-quick-btn');
        if (btn && !isLoading) {
          document.getElementById('cw-input').value = btn.getAttribute('data-msg');
          sendMessage();
          quickActions.style.display = 'none';
        }
      });
    }
  }

  function toggleWindow() {
    isOpen = !isOpen;
    document.getElementById('cw-window').classList.toggle('cw-visible', isOpen);
    document.getElementById('cw-toggle').classList.toggle('cw-open', isOpen);
    if (isOpen) document.getElementById('cw-input').focus();
  }

  function addMessage(text, type) {
    const messages = document.getElementById('cw-messages');
    const msg = document.createElement('div');
    msg.className = `cw-msg cw-msg-${type}`;
    msg.textContent = type === 'bot' ? stripMarkdown(text) : text;
    messages.appendChild(msg);
    messages.scrollTop = messages.scrollHeight;
  }

  function showTyping() {
    const messages = document.getElementById('cw-messages');
    const typing = document.createElement('div');
    typing.className = 'cw-typing';
    typing.id = 'cw-typing';
    typing.innerHTML = '<span></span><span></span><span></span>';
    messages.appendChild(typing);
    messages.scrollTop = messages.scrollHeight;
  }

  function hideTyping() {
    const el = document.getElementById('cw-typing');
    if (el) el.remove();
  }

  function setLoading(loading) {
    isLoading = loading;
    const input = document.getElementById('cw-input');
    document.getElementById('cw-send').disabled = loading || !input.value.trim();
    input.disabled = loading;
  }

  async function sendMessage() {
    const input = document.getElementById('cw-input');
    const text = input.value.trim();
    if (!text) return;

    input.value = '';
    input.style.height = 'auto';
    addMessage(text, 'user');
    setLoading(true);
    showTyping();

    try {
      const response = await fetch(`${CONFIG.apiUrl}/api/v1/ask`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': CONFIG.apiKey,
        },
        body: JSON.stringify({
          user_id: 'widget-user',
          session_id: sessionId,
          message: text,
        }),
      });

      if (!response.ok) throw new Error(`API error: ${response.status}`);

      const { run_id } = await response.json();
      await pollForResult(run_id);
    } catch (err) {
      hideTyping();
      addMessage("Sorry, I'm having trouble connecting. Please try again.", 'bot');
      console.error('[ChatWidget]', err);
    } finally {
      setLoading(false);
    }
  }

  async function pollForResult(runId) {
    for (let i = 0; i < MAX_POLLS; i++) {
      await new Promise((r) => setTimeout(r, POLL_INTERVAL));

      const response = await fetch(`${CONFIG.apiUrl}/api/v1/runs/${runId}`, {
        headers: { 'X-API-Key': CONFIG.apiKey },
      });

      if (!response.ok) continue;
      const data = await response.json();

      if (data.status === 'done') {
        hideTyping();
        addMessage(data.answer || 'No response received.', 'bot');
        return;
      }

      if (data.status === 'failed') {
        hideTyping();
        addMessage(data.error || 'Sorry, something went wrong.', 'bot');
        return;
      }
    }

    hideTyping();
    addMessage('Sorry, the response is taking too long. Please try again.', 'bot');
  }

  // --- Init ---
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', createWidget);
  } else {
    createWidget();
  }
})();
