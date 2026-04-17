(function () {
  'use strict';

  const WIDGET_ID = 'nalla-chat-widget';
  const script = document.currentScript;
  const API_BASE = script?.getAttribute('data-api-url') || '';
  const API_KEY = script?.getAttribute('data-api-key') || '';
  const POSITION = script?.getAttribute('data-position') || 'right';
  const POLL_INTERVAL = 1000;
  const MAX_POLLS = 60;

  // --- State ---
  let isOpen = false;
  let isLoading = false;
  let sessionId = `sess_${crypto.randomUUID()}`;

  // --- Styles ---
  const styles = `
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');

    #${WIDGET_ID} {
      --nw-primary: #4f46e5;
      --nw-primary-hover: #4338ca;
      --nw-primary-light: #eef2ff;
      --nw-accent: #f59e0b;
      --nw-bg: #ffffff;
      --nw-bg-chat: #f8fafc;
      --nw-text: #1e293b;
      --nw-text-light: #64748b;
      --nw-border: #e2e8f0;
      --nw-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
      --nw-radius: 16px;
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
      position: fixed;
      bottom: 24px;
      ${POSITION === 'left' ? 'left: 24px;' : 'right: 24px;'}
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

    /* --- Toggle Button --- */
    .nw-toggle {
      width: 64px;
      height: 64px;
      border-radius: 50%;
      border: none;
      background: var(--nw-primary);
      color: white;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      box-shadow: 0 4px 20px rgba(79, 70, 229, 0.4);
      transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
      position: relative;
      overflow: hidden;
    }

    .nw-toggle:hover {
      transform: scale(1.08);
      box-shadow: 0 6px 28px rgba(79, 70, 229, 0.5);
    }

    .nw-toggle:active {
      transform: scale(0.95);
    }

    .nw-toggle svg {
      width: 28px;
      height: 28px;
      transition: all 0.3s ease;
    }

    .nw-toggle .nw-icon-close {
      position: absolute;
      opacity: 0;
      transform: rotate(-90deg) scale(0.5);
    }

    .nw-toggle.nw-open .nw-icon-paw {
      opacity: 0;
      transform: rotate(90deg) scale(0.5);
    }

    .nw-toggle.nw-open .nw-icon-close {
      opacity: 1;
      transform: rotate(0) scale(1);
    }

    .nw-toggle .nw-pulse {
      position: absolute;
      width: 100%;
      height: 100%;
      border-radius: 50%;
      background: var(--nw-primary);
      animation: nw-pulse 2s ease-in-out infinite;
      z-index: -1;
    }

    @keyframes nw-pulse {
      0%, 100% { transform: scale(1); opacity: 0.4; }
      50% { transform: scale(1.2); opacity: 0; }
    }

    /* --- Chat Window --- */
    .nw-window {
      position: absolute;
      bottom: 80px;
      ${POSITION === 'left' ? 'left: 0;' : 'right: 0;'}
      width: 400px;
      max-width: calc(100vw - 48px);
      height: 560px;
      max-height: calc(100vh - 140px);
      background: var(--nw-bg);
      border-radius: var(--nw-radius);
      box-shadow: var(--nw-shadow);
      display: flex;
      flex-direction: column;
      overflow: hidden;
      opacity: 0;
      transform: translateY(20px) scale(0.95);
      pointer-events: none;
      transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1);
      border: 1px solid var(--nw-border);
    }

    .nw-window.nw-visible {
      opacity: 1;
      transform: translateY(0) scale(1);
      pointer-events: all;
    }

    /* --- Header --- */
    .nw-header {
      background: linear-gradient(135deg, var(--nw-primary) 0%, #6366f1 100%);
      color: white;
      padding: 20px;
      display: flex;
      align-items: center;
      gap: 12px;
      flex-shrink: 0;
    }

    .nw-avatar {
      width: 44px;
      height: 44px;
      border-radius: 50%;
      background: rgba(255, 255, 255, 0.2);
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 22px;
      flex-shrink: 0;
    }

    .nw-header-text h3 {
      font-size: 16px;
      font-weight: 600;
      margin: 0;
    }

    .nw-header-text p {
      font-size: 12px;
      opacity: 0.85;
      margin: 2px 0 0;
    }

    .nw-status-dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: #4ade80;
      display: inline-block;
      margin-right: 4px;
      animation: nw-glow 2s ease-in-out infinite;
    }

    @keyframes nw-glow {
      0%, 100% { box-shadow: 0 0 4px rgba(74, 222, 128, 0.4); }
      50% { box-shadow: 0 0 8px rgba(74, 222, 128, 0.8); }
    }

    /* --- Messages --- */
    .nw-messages {
      flex: 1;
      overflow-y: auto;
      padding: 16px;
      background: var(--nw-bg-chat);
      display: flex;
      flex-direction: column;
      gap: 12px;
      scroll-behavior: smooth;
    }

    .nw-messages::-webkit-scrollbar {
      width: 5px;
    }

    .nw-messages::-webkit-scrollbar-track {
      background: transparent;
    }

    .nw-messages::-webkit-scrollbar-thumb {
      background: var(--nw-border);
      border-radius: 10px;
    }

    .nw-msg {
      max-width: 85%;
      padding: 10px 14px;
      border-radius: 14px;
      font-size: 14px;
      line-height: 1.5;
      animation: nw-fade-in 0.3s ease;
      word-wrap: break-word;
      overflow-wrap: anywhere;
      word-break: break-word;
      white-space: pre-wrap;
      overflow: hidden;
    }

    @keyframes nw-fade-in {
      from { opacity: 0; transform: translateY(8px); }
      to { opacity: 1; transform: translateY(0); }
    }

    .nw-msg-user {
      align-self: flex-end;
      background: var(--nw-primary);
      color: white;
      border-bottom-right-radius: 4px;
    }

    .nw-msg-bot {
      align-self: flex-start;
      background: white;
      color: var(--nw-text);
      border: 1px solid var(--nw-border);
      border-bottom-left-radius: 4px;
    }

    .nw-msg-welcome {
      align-self: center;
      background: var(--nw-primary-light);
      color: var(--nw-primary);
      border-radius: 12px;
      text-align: center;
      font-size: 13px;
      max-width: 100%;
      padding: 12px 16px;
    }

    /* --- Typing indicator --- */
    .nw-typing {
      align-self: flex-start;
      display: flex;
      gap: 4px;
      padding: 12px 16px;
      background: white;
      border: 1px solid var(--nw-border);
      border-radius: 14px;
      border-bottom-left-radius: 4px;
    }

    .nw-typing span {
      width: 7px;
      height: 7px;
      border-radius: 50%;
      background: var(--nw-text-light);
      animation: nw-bounce 1.4s ease-in-out infinite;
    }

    .nw-typing span:nth-child(2) { animation-delay: 0.2s; }
    .nw-typing span:nth-child(3) { animation-delay: 0.4s; }

    @keyframes nw-bounce {
      0%, 60%, 100% { transform: translateY(0); opacity: 0.4; }
      30% { transform: translateY(-6px); opacity: 1; }
    }

    /* --- Quick Actions --- */
    .nw-quick-actions {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      padding: 0 16px 12px;
      background: var(--nw-bg-chat);
    }

    .nw-quick-btn {
      padding: 6px 12px;
      border-radius: 20px;
      border: 1px solid var(--nw-border);
      background: white;
      color: var(--nw-text);
      font-size: 12px;
      cursor: pointer;
      transition: all 0.2s;
      font-family: inherit;
    }

    .nw-quick-btn:hover {
      border-color: var(--nw-primary);
      color: var(--nw-primary);
      background: var(--nw-primary-light);
    }

    /* --- Input --- */
    .nw-input-area {
      padding: 12px 16px;
      border-top: 1px solid var(--nw-border);
      display: flex;
      gap: 8px;
      align-items: flex-end;
      background: var(--nw-bg);
    }

    .nw-input {
      flex: 1;
      border: 1px solid var(--nw-border);
      border-radius: 12px;
      padding: 10px 14px;
      font-size: 14px;
      font-family: inherit;
      outline: none;
      resize: none;
      max-height: 80px;
      line-height: 1.4;
      transition: border-color 0.2s;
      color: var(--nw-text);
      background: var(--nw-bg-chat);
    }

    .nw-input::placeholder {
      color: var(--nw-text-light);
    }

    .nw-input:focus {
      border-color: var(--nw-primary);
    }

    .nw-send {
      width: 40px;
      height: 40px;
      border-radius: 10px;
      border: none;
      background: var(--nw-primary);
      color: white;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: all 0.2s;
      flex-shrink: 0;
    }

    .nw-send:hover:not(:disabled) {
      background: var(--nw-primary-hover);
    }

    .nw-send:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }

    .nw-send svg {
      width: 18px;
      height: 18px;
    }

    /* --- Footer --- */
    .nw-footer {
      text-align: center;
      padding: 8px;
      font-size: 11px;
      color: var(--nw-text-light);
      background: var(--nw-bg);
      border-top: 1px solid var(--nw-border);
    }

    .nw-footer a {
      color: var(--nw-primary);
      text-decoration: none;
    }

    /* --- Mobile --- */
    @media (max-width: 480px) {
      .nw-window {
        width: calc(100vw - 16px);
        height: calc(100vh - 100px);
        bottom: 76px;
        ${POSITION === 'left' ? 'left: -16px;' : 'right: -16px;'}
        border-radius: 12px;
      }

      .nw-toggle {
        width: 56px;
        height: 56px;
      }
    }
  `;

  // --- Icons ---
  const pawIcon = `<svg viewBox="0 0 24 24" fill="currentColor"><path d="M8.35 3c1.18-.17 2.43 1.12 2.79 2.9.36 1.77-.29 3.35-1.47 3.53-1.17.18-2.43-1.11-2.8-2.89-.37-1.77.3-3.36 1.48-3.54zm7.15 0c1.18.18 1.85 1.77 1.48 3.54-.37 1.78-1.63 3.07-2.8 2.89-1.18-.18-1.83-1.76-1.47-3.53.36-1.78 1.61-3.07 2.79-2.9zM3.05 10.13c1.07-.63 2.62.05 3.46 1.52.84 1.47.68 3.13-.39 3.76-1.07.63-2.62-.06-3.46-1.53-.84-1.47-.68-3.12.39-3.75zm17.9 0c1.07.63 1.23 2.28.39 3.75-.84 1.47-2.39 2.16-3.46 1.53-1.07-.63-1.23-2.29-.39-3.76.84-1.47 2.39-2.15 3.46-1.52zM12 13.5c2.76 0 5 1.79 5 4 0 2.21-2.24 4-5 4s-5-1.79-5-4c0-2.21 2.24-4 5-4z"/></svg>`;
  const closeIcon = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>`;
  const sendIcon = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>`;

  // --- Build DOM ---
  function createWidget() {
    const container = document.createElement('div');
    container.id = WIDGET_ID;

    const styleEl = document.createElement('style');
    styleEl.textContent = styles;
    container.appendChild(styleEl);

    container.innerHTML += `
      <div class="nw-window" id="nw-window">
        <div class="nw-header">
          <div class="nw-avatar">${pawIcon.replace('width="28"', 'width="24"')}</div>
          <div class="nw-header-text">
            <h3>Nalla's Dad</h3>
            <p><span class="nw-status-dot"></span>Dog food safety expert</p>
          </div>
        </div>
        <div class="nw-messages" id="nw-messages">
          <div class="nw-msg nw-msg-welcome">
            Hey there! I'm Nalla's Dad. Ask me if any food is safe for your dog.
          </div>
        </div>
        <div class="nw-quick-actions" id="nw-quick-actions">
          <button class="nw-quick-btn" data-msg="Can my dog eat chocolate?">Chocolate?</button>
          <button class="nw-quick-btn" data-msg="Is rice safe for dogs?">Rice?</button>
          <button class="nw-quick-btn" data-msg="Can dogs eat grapes?">Grapes?</button>
          <button class="nw-quick-btn" data-msg="Is peanut butter safe?">Peanut butter?</button>
        </div>
        <div class="nw-input-area">
          <textarea class="nw-input" id="nw-input" placeholder="Ask about any food..." rows="1"></textarea>
          <button class="nw-send" id="nw-send" disabled>${sendIcon}</button>
        </div>
        <div class="nw-footer">
          Powered by <a href="https://dogfoodandfun.com" target="_blank">Dog Food & Fun</a>
        </div>
      </div>
      <button class="nw-toggle" id="nw-toggle">
        <span class="nw-pulse"></span>
        <span class="nw-icon-paw">${pawIcon}</span>
        <span class="nw-icon-close">${closeIcon}</span>
      </button>
    `;

    document.body.appendChild(container);
    bindEvents();
  }

  // --- Events ---
  function bindEvents() {
    const toggle = document.getElementById('nw-toggle');
    const input = document.getElementById('nw-input');
    const send = document.getElementById('nw-send');
    const quickActions = document.getElementById('nw-quick-actions');

    toggle.addEventListener('click', toggleWindow);

    input.addEventListener('input', () => {
      send.disabled = !input.value.trim() || isLoading;
      // Auto-resize
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

    quickActions.addEventListener('click', (e) => {
      const btn = e.target.closest('.nw-quick-btn');
      if (btn && !isLoading) {
        const msg = btn.getAttribute('data-msg');
        input.value = msg;
        sendMessage();
        quickActions.style.display = 'none';
      }
    });
  }

  function toggleWindow() {
    isOpen = !isOpen;
    const win = document.getElementById('nw-window');
    const toggle = document.getElementById('nw-toggle');
    win.classList.toggle('nw-visible', isOpen);
    toggle.classList.toggle('nw-open', isOpen);
    if (isOpen) {
      document.getElementById('nw-input').focus();
    }
  }

  // --- Text cleanup ---
  function stripMarkdown(text) {
    return text
      .replace(/#{1,6}\s+/g, '')           // headers
      .replace(/\*\*(.+?)\*\*/g, '$1')     // bold
      .replace(/\*(.+?)\*/g, '$1')         // italic
      .replace(/__(.+?)__/g, '$1')         // bold alt
      .replace(/_(.+?)_/g, '$1')           // italic alt
      .replace(/`(.+?)`/g, '$1')           // inline code
      .replace(/^\s*[-*+]\s+/gm, '- ')     // normalize list markers
      .replace(/^\s*\d+\.\s+/gm, '')       // numbered lists
      .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1') // links
      .replace(/\n{3,}/g, '\n\n')          // collapse extra newlines
      .trim();
  }

  // --- Messaging ---
  function addMessage(text, type) {
    const messages = document.getElementById('nw-messages');
    const msg = document.createElement('div');
    msg.className = `nw-msg nw-msg-${type}`;
    msg.textContent = type === 'bot' ? stripMarkdown(text) : text;
    messages.appendChild(msg);
    messages.scrollTop = messages.scrollHeight;
    return msg;
  }

  function showTyping() {
    const messages = document.getElementById('nw-messages');
    const typing = document.createElement('div');
    typing.className = 'nw-typing';
    typing.id = 'nw-typing';
    typing.innerHTML = '<span></span><span></span><span></span>';
    messages.appendChild(typing);
    messages.scrollTop = messages.scrollHeight;
  }

  function hideTyping() {
    const typing = document.getElementById('nw-typing');
    if (typing) typing.remove();
  }

  function setLoading(loading) {
    isLoading = loading;
    const send = document.getElementById('nw-send');
    const input = document.getElementById('nw-input');
    send.disabled = loading || !input.value.trim();
    input.disabled = loading;
  }

  async function sendMessage() {
    const input = document.getElementById('nw-input');
    const text = input.value.trim();
    if (!text) return;

    input.value = '';
    input.style.height = 'auto';
    addMessage(text, 'user');
    setLoading(true);
    showTyping();

    try {
      const response = await fetch(`${API_BASE}/api/v1/ask`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': API_KEY,
        },
        body: JSON.stringify({
          user_id: 'widget-user',
          session_id: sessionId,
          message: text,
        }),
      });

      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }

      const { run_id } = await response.json();
      await pollForResult(run_id);
    } catch (err) {
      hideTyping();
      addMessage("Sorry, I'm having trouble connecting. Please try again.", 'bot');
      console.error('[Nalla Widget]', err);
    } finally {
      setLoading(false);
    }
  }

  async function pollForResult(runId) {
    for (let i = 0; i < MAX_POLLS; i++) {
      await new Promise((r) => setTimeout(r, POLL_INTERVAL));

      const response = await fetch(`${API_BASE}/api/v1/runs/${runId}`, {
        headers: { 'X-API-Key': API_KEY },
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
        addMessage(
          data.error || "Sorry, something went wrong. Please try again.",
          'bot'
        );
        return;
      }
    }

    hideTyping();
    addMessage("Sorry, the response is taking too long. Please try again.", 'bot');
  }

  // --- Init ---
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', createWidget);
  } else {
    createWidget();
  }
})();
