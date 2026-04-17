(function () {
  'use strict';

  const WIDGET_ID = 'llm-chat-widget';
  const script = document.currentScript;

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
    primaryColor: script?.getAttribute('data-primary-color') || '#2563eb',
    icon: script?.getAttribute('data-icon') || 'chat',
    quickActions: script?.getAttribute('data-quick-actions') || '',
  };

  const POLL_INTERVAL = 1000;
  const MAX_POLLS = 60;
  let isOpen = false;
  let isLoading = false;
  let sessionId = `sess_${crypto.randomUUID()}`;

  // --- Icons ---
  const ICONS = {
    chat: '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2z"/></svg>',
    paw: '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M8.35 3c1.18-.17 2.43 1.12 2.79 2.9.36 1.77-.29 3.35-1.47 3.53-1.17.18-2.43-1.11-2.8-2.89-.37-1.77.3-3.36 1.48-3.54zm7.15 0c1.18.18 1.85 1.77 1.48 3.54-.37 1.78-1.63 3.07-2.8 2.89-1.18-.18-1.83-1.76-1.47-3.53.36-1.78 1.61-3.07 2.79-2.9zM3.05 10.13c1.07-.63 2.62.05 3.46 1.52.84 1.47.68 3.13-.39 3.76-1.07.63-2.62-.06-3.46-1.53-.84-1.47-.68-3.12.39-3.75zm17.9 0c1.07.63 1.23 2.28.39 3.75-.84 1.47-2.39 2.16-3.46 1.53-1.07-.63-1.23-2.29-.39-3.76.84-1.47 2.39-2.15 3.46-1.52zM12 13.5c2.76 0 5 1.79 5 4 0 2.21-2.24 4-5 4s-5-1.79-5-4c0-2.21 2.24-4 5-4z"/></svg>',
    bot: '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 2a2 2 0 0 1 2 2c0 .74-.4 1.39-1 1.73V7h1a7 7 0 0 1 7 7h1a1 1 0 0 1 1 1v3a1 1 0 0 1-1 1h-1v1a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2v-1H3a1 1 0 0 1-1-1v-3a1 1 0 0 1 1-1h1a7 7 0 0 1 7-7h1V5.73A2 2 0 0 1 12 2zM9.5 13a1.5 1.5 0 1 0 0 3 1.5 1.5 0 0 0 0-3zm5 0a1.5 1.5 0 1 0 0 3 1.5 1.5 0 0 0 0-3z"/></svg>',
  };
  const closeIcon = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>';
  const sendIcon = '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/></svg>';

  function getIcon() {
    if (CONFIG.icon.startsWith('http') || CONFIG.icon.startsWith('/'))
      return `<img src="${CONFIG.icon}" alt="" style="width:100%;height:100%;object-fit:cover;border-radius:50%">`;
    return ICONS[CONFIG.icon] || ICONS.chat;
  }

  // --- Styles ---
  const styles = `
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');

    #${WIDGET_ID} {
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
      position: fixed;
      bottom: 20px;
      ${CONFIG.position === 'left' ? 'left: 20px;' : 'right: 20px;'}
      z-index: 999999;
      font-size: 14px;
      line-height: 1.5;
    }

    #${WIDGET_ID} *, #${WIDGET_ID} *::before, #${WIDGET_ID} *::after {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }

    /* ---- Launcher ---- */
    .cw-launcher {
      width: 60px;
      height: 60px;
      border-radius: 50%;
      border: none;
      background: ${CONFIG.primaryColor};
      color: #fff;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      box-shadow: 0 4px 12px rgba(0,0,0,0.15);
      transition: transform 0.2s, box-shadow 0.2s;
    }
    .cw-launcher:hover {
      transform: scale(1.05);
      box-shadow: 0 6px 20px rgba(0,0,0,0.2);
    }
    .cw-launcher svg { width: 26px; height: 26px; transition: transform 0.3s; }
    .cw-launcher .cw-close-icon {
      position: absolute;
      opacity: 0;
      transform: rotate(-90deg) scale(0);
      transition: all 0.3s;
    }
    .cw-launcher.cw-open .cw-main-icon { opacity: 0; transform: rotate(90deg) scale(0); }
    .cw-launcher.cw-open .cw-close-icon { opacity: 1; transform: rotate(0) scale(1); }

    /* ---- Window ---- */
    .cw-window {
      position: absolute;
      bottom: 72px;
      ${CONFIG.position === 'left' ? 'left: 0;' : 'right: 0;'}
      width: 380px;
      max-width: calc(100vw - 40px);
      height: 520px;
      max-height: calc(100vh - 120px);
      background: #fff;
      border-radius: 16px;
      box-shadow: 0 5px 40px rgba(0,0,0,0.16);
      display: flex;
      flex-direction: column;
      overflow: hidden;
      opacity: 0;
      transform: translateY(16px) scale(0.96);
      pointer-events: none;
      transition: opacity 0.25s ease, transform 0.25s ease;
    }
    .cw-window.cw-open { opacity: 1; transform: translateY(0) scale(1); pointer-events: all; }

    /* ---- Header ---- */
    .cw-header {
      background: ${CONFIG.primaryColor};
      color: #fff;
      padding: 18px 20px;
      display: flex;
      align-items: center;
      gap: 12px;
      flex-shrink: 0;
    }
    .cw-avatar {
      width: 40px;
      height: 40px;
      border-radius: 50%;
      background: rgba(255,255,255,0.2);
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
    }
    .cw-avatar svg { width: 22px; height: 22px; color: #fff; }
    .cw-header-info h3 { font-size: 15px; font-weight: 600; }
    .cw-header-info p { font-size: 12px; opacity: 0.85; margin-top: 1px; }
    .cw-online-dot {
      display: inline-block;
      width: 7px; height: 7px;
      background: #34d399;
      border-radius: 50%;
      margin-right: 5px;
      vertical-align: middle;
    }

    /* ---- Messages ---- */
    .cw-messages {
      flex: 1;
      overflow-y: auto;
      padding: 16px;
      background: #f0f4f8;
      display: flex;
      flex-direction: column;
      gap: 10px;
    }
    .cw-messages::-webkit-scrollbar { width: 4px; }
    .cw-messages::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 4px; }

    .cw-bubble {
      max-width: 80%;
      padding: 10px 14px;
      font-size: 14px;
      line-height: 1.5;
      animation: cw-slide-in 0.2s ease;
      word-wrap: break-word;
      overflow-wrap: anywhere;
    }
    @keyframes cw-slide-in {
      from { opacity: 0; transform: translateY(6px); }
      to { opacity: 1; transform: translateY(0); }
    }

    .cw-bubble-user {
      align-self: flex-end;
      background: ${CONFIG.primaryColor};
      color: #fff;
      border-radius: 16px 16px 4px 16px;
    }
    .cw-bubble-bot {
      align-self: flex-start;
      background: #fff;
      color: #1e293b;
      border-radius: 16px 16px 16px 4px;
      box-shadow: 0 1px 3px rgba(0,0,0,0.08);
    }
    .cw-bubble-welcome {
      align-self: flex-start;
      background: #fff;
      color: #475569;
      border-radius: 16px 16px 16px 4px;
      box-shadow: 0 1px 3px rgba(0,0,0,0.08);
      font-size: 13px;
    }

    /* ---- Typing ---- */
    .cw-typing {
      align-self: flex-start;
      display: flex;
      gap: 5px;
      padding: 12px 18px;
      background: #fff;
      border-radius: 16px 16px 16px 4px;
      box-shadow: 0 1px 3px rgba(0,0,0,0.08);
    }
    .cw-typing span {
      width: 6px; height: 6px;
      border-radius: 50%;
      background: #94a3b8;
      animation: cw-dot 1.2s ease-in-out infinite;
    }
    .cw-typing span:nth-child(2) { animation-delay: 0.15s; }
    .cw-typing span:nth-child(3) { animation-delay: 0.3s; }
    @keyframes cw-dot {
      0%, 60%, 100% { transform: translateY(0); }
      30% { transform: translateY(-5px); }
    }

    /* ---- Quick Actions ---- */
    .cw-actions {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      padding: 8px 16px 12px;
      background: #f0f4f8;
      flex-shrink: 0;
    }
    .cw-action-btn {
      padding: 6px 14px;
      border-radius: 16px;
      border: 1.5px solid ${CONFIG.primaryColor};
      background: #fff;
      color: ${CONFIG.primaryColor};
      font-size: 12px;
      font-weight: 500;
      cursor: pointer;
      font-family: inherit;
      transition: background 0.15s, color 0.15s;
    }
    .cw-action-btn:hover {
      background: ${CONFIG.primaryColor};
      color: #fff;
    }

    /* ---- Input ---- */
    .cw-input-row {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 10px 14px;
      border-top: 1px solid #e2e8f0;
      background: #fff;
      flex-shrink: 0;
    }
    .cw-input {
      flex: 1;
      border: 1px solid #e2e8f0;
      border-radius: 20px;
      padding: 9px 16px;
      font-size: 13px;
      font-family: inherit;
      outline: none;
      resize: none;
      max-height: 72px;
      line-height: 1.4;
      color: #1e293b;
      background: #f8fafc;
    }
    .cw-input::placeholder { color: #94a3b8; }
    .cw-input:focus { border-color: ${CONFIG.primaryColor}; background: #fff; }

    .cw-send-btn {
      width: 36px;
      height: 36px;
      border-radius: 50%;
      border: none;
      background: ${CONFIG.primaryColor};
      color: #fff;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
      transition: opacity 0.15s;
    }
    .cw-send-btn:disabled { opacity: 0.4; cursor: default; }
    .cw-send-btn svg { width: 16px; height: 16px; }

    /* ---- Footer ---- */
    .cw-footer {
      text-align: center;
      padding: 6px;
      font-size: 10px;
      color: #94a3b8;
      background: #fff;
      flex-shrink: 0;
    }
    .cw-footer a { color: ${CONFIG.primaryColor}; text-decoration: none; font-weight: 500; }

    /* ---- Mobile ---- */
    @media (max-width: 480px) {
      .cw-window {
        width: calc(100vw - 16px);
        height: calc(100vh - 90px);
        bottom: 70px;
        border-radius: 12px;
        ${CONFIG.position === 'left' ? 'left: -12px;' : 'right: -12px;'}
      }
      .cw-launcher { width: 52px; height: 52px; }
    }
  `;

  // --- Helpers ---
  function stripMarkdown(t) {
    return t.replace(/#{1,6}\s+/g,'').replace(/\*\*(.+?)\*\*/g,'$1').replace(/\*(.+?)\*/g,'$1')
      .replace(/__(.+?)__/g,'$1').replace(/_(.+?)_/g,'$1').replace(/`(.+?)`/g,'$1')
      .replace(/^\s*[-*+]\s+/gm,'').replace(/^\s*\d+\.\s+/gm,'')
      .replace(/\[([^\]]+)\]\([^)]+\)/g,'$1').replace(/\n{3,}/g,'\n\n').trim();
  }

  function buildActions() {
    if (!CONFIG.quickActions) return '';
    const btns = CONFIG.quickActions.split('|').filter(Boolean)
      .map(a => `<button class="cw-action-btn" data-msg="${a.trim()}">${a.trim()}</button>`).join('');
    return `<div class="cw-actions" id="cw-actions">${btns}</div>`;
  }

  function buildFooter() {
    if (!CONFIG.footerText) return '';
    const inner = CONFIG.footerUrl
      ? `<a href="${CONFIG.footerUrl}" target="_blank">${CONFIG.footerText}</a>`
      : CONFIG.footerText;
    return `<div class="cw-footer">Powered by ${inner}</div>`;
  }

  // --- DOM ---
  function createWidget() {
    const el = document.createElement('div');
    el.id = WIDGET_ID;
    const s = document.createElement('style');
    s.textContent = styles;
    el.appendChild(s);

    el.innerHTML += `
      <div class="cw-window" id="cw-window">
        <div class="cw-header">
          <div class="cw-avatar">${getIcon()}</div>
          <div class="cw-header-info">
            <h3>${CONFIG.title}</h3>
            <p><span class="cw-online-dot"></span>${CONFIG.subtitle}</p>
          </div>
        </div>
        <div class="cw-messages" id="cw-messages">
          <div class="cw-bubble cw-bubble-welcome">${CONFIG.welcome}</div>
        </div>
        ${buildActions()}
        <div class="cw-input-row">
          <textarea class="cw-input" id="cw-input" placeholder="${CONFIG.placeholder}" rows="1"></textarea>
          <button class="cw-send-btn" id="cw-send" disabled>${sendIcon}</button>
        </div>
        ${buildFooter()}
      </div>
      <button class="cw-launcher" id="cw-launcher">
        <span class="cw-main-icon">${getIcon()}</span>
        <span class="cw-close-icon">${closeIcon}</span>
      </button>
    `;
    document.body.appendChild(el);
    bind();
  }

  // --- Events ---
  function bind() {
    const launcher = document.getElementById('cw-launcher');
    const input = document.getElementById('cw-input');
    const send = document.getElementById('cw-send');
    const actions = document.getElementById('cw-actions');

    launcher.addEventListener('click', toggle);
    input.addEventListener('input', () => {
      send.disabled = !input.value.trim() || isLoading;
      input.style.height = 'auto';
      input.style.height = Math.min(input.scrollHeight, 72) + 'px';
    });
    input.addEventListener('keydown', e => {
      if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); if (input.value.trim() && !isLoading) send_msg(); }
    });
    send.addEventListener('click', () => { if (input.value.trim() && !isLoading) send_msg(); });
    if (actions) actions.addEventListener('click', e => {
      const b = e.target.closest('.cw-action-btn');
      if (b && !isLoading) { document.getElementById('cw-input').value = b.dataset.msg; send_msg(); actions.style.display = 'none'; }
    });
  }

  function toggle() {
    isOpen = !isOpen;
    document.getElementById('cw-window').classList.toggle('cw-open', isOpen);
    document.getElementById('cw-launcher').classList.toggle('cw-open', isOpen);
    if (isOpen) document.getElementById('cw-input').focus();
  }

  function addBubble(text, type) {
    const area = document.getElementById('cw-messages');
    const d = document.createElement('div');
    d.className = `cw-bubble cw-bubble-${type}`;
    d.textContent = type === 'bot' ? stripMarkdown(text) : text;
    area.appendChild(d);
    area.scrollTop = area.scrollHeight;
  }

  function showTyping() {
    const area = document.getElementById('cw-messages');
    const d = document.createElement('div'); d.className = 'cw-typing'; d.id = 'cw-typing';
    d.innerHTML = '<span></span><span></span><span></span>';
    area.appendChild(d); area.scrollTop = area.scrollHeight;
  }
  function hideTyping() { document.getElementById('cw-typing')?.remove(); }

  function setLoading(v) {
    isLoading = v;
    const inp = document.getElementById('cw-input');
    document.getElementById('cw-send').disabled = v || !inp.value.trim();
    inp.disabled = v;
  }

  async function send_msg() {
    const inp = document.getElementById('cw-input');
    const text = inp.value.trim(); if (!text) return;
    inp.value = ''; inp.style.height = 'auto';
    addBubble(text, 'user'); setLoading(true); showTyping();
    try {
      const r = await fetch(`${CONFIG.apiUrl}/api/v1/ask`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-API-Key': CONFIG.apiKey },
        body: JSON.stringify({ user_id: 'widget-user', session_id: sessionId, message: text }),
      });
      if (!r.ok) throw new Error(r.status);
      const { run_id } = await r.json();
      await poll(run_id);
    } catch (e) {
      hideTyping();
      addBubble("Sorry, I'm having trouble connecting. Please try again.", 'bot');
    } finally { setLoading(false); }
  }

  async function poll(id) {
    for (let i = 0; i < MAX_POLLS; i++) {
      await new Promise(r => setTimeout(r, POLL_INTERVAL));
      try {
        const r = await fetch(`${CONFIG.apiUrl}/api/v1/runs/${id}`, { headers: { 'X-API-Key': CONFIG.apiKey } });
        if (!r.ok) continue;
        const d = await r.json();
        if (d.status === 'done') { hideTyping(); addBubble(d.answer || 'No response.', 'bot'); return; }
        if (d.status === 'failed') { hideTyping(); addBubble(d.error || 'Something went wrong.', 'bot'); return; }
      } catch { continue; }
    }
    hideTyping(); addBubble('Response took too long. Please try again.', 'bot');
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', createWidget);
  else createWidget();
})();
