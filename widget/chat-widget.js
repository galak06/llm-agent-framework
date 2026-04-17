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

  const ICONS = {
    chat: '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2z"/></svg>',
    paw: '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M8.35 3c1.18-.17 2.43 1.12 2.79 2.9.36 1.77-.29 3.35-1.47 3.53-1.17.18-2.43-1.11-2.8-2.89-.37-1.77.3-3.36 1.48-3.54zm7.15 0c1.18.18 1.85 1.77 1.48 3.54-.37 1.78-1.63 3.07-2.8 2.89-1.18-.18-1.83-1.76-1.47-3.53.36-1.78 1.61-3.07 2.79-2.9zM3.05 10.13c1.07-.63 2.62.05 3.46 1.52.84 1.47.68 3.13-.39 3.76-1.07.63-2.62-.06-3.46-1.53-.84-1.47-.68-3.12.39-3.75zm17.9 0c1.07.63 1.23 2.28.39 3.75-.84 1.47-2.39 2.16-3.46 1.53-1.07-.63-1.23-2.29-.39-3.76.84-1.47 2.39-2.15 3.46-1.52zM12 13.5c2.76 0 5 1.79 5 4 0 2.21-2.24 4-5 4s-5-1.79-5-4c0-2.21 2.24-4 5-4z"/></svg>',
    bot: '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 2a2 2 0 0 1 2 2c0 .74-.4 1.39-1 1.73V7h1a7 7 0 0 1 7 7h1a1 1 0 0 1 1 1v3a1 1 0 0 1-1 1h-1v1a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2v-1H3a1 1 0 0 1-1-1v-3a1 1 0 0 1 1-1h1a7 7 0 0 1 7-7h1V5.73A2 2 0 0 1 12 2zM9.5 13a1.5 1.5 0 1 0 0 3 1.5 1.5 0 0 0 0-3zm5 0a1.5 1.5 0 1 0 0 3 1.5 1.5 0 0 0 0-3z"/></svg>',
  };
  const closeIcon = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>';
  const sendIcon = '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/></svg>';

  function getIcon() {
    if (CONFIG.icon.startsWith('http') || CONFIG.icon.startsWith('/'))
      return `<img src="${CONFIG.icon}" alt="">`;
    return ICONS[CONFIG.icon] || ICONS.chat;
  }

  function stripMarkdown(t) {
    return t.replace(/#{1,6}\s+/g, '').replace(/\*\*(.+?)\*\*/g, '$1').replace(/\*(.+?)\*/g, '$1')
      .replace(/__(.+?)__/g, '$1').replace(/_(.+?)_/g, '$1').replace(/`(.+?)`/g, '$1')
      .replace(/^\s*[-*+]\s+/gm, '').replace(/^\s*\d+\.\s+/gm, '')
      .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1').replace(/\n{3,}/g, '\n\n').trim();
  }

  // --- Styles ---
  const PC = CONFIG.primaryColor;
  const styles = document.createElement('style');
  styles.textContent = `
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');

    #${WIDGET_ID} {
      font-family: 'Inter', system-ui, -apple-system, sans-serif;
      position: fixed;
      bottom: 24px;
      ${CONFIG.position === 'left' ? 'left: 24px;' : 'right: 24px;'}
      z-index: 999999;
      font-size: 14px;
      line-height: 1.5;
    }
    #${WIDGET_ID} * { box-sizing: border-box; margin: 0; padding: 0; }

    /* Launcher */
    .cw-launcher {
      width: 60px; height: 60px; border-radius: 50%; border: none;
      background: ${PC}; color: #fff; cursor: pointer;
      display: flex; align-items: center; justify-content: center;
      box-shadow: 0 4px 14px rgba(0,0,0,0.15);
      transition: transform 0.2s ease;
      position: relative;
    }
    .cw-launcher:hover { transform: scale(1.05); }
    .cw-launcher svg { width: 26px; height: 26px; }
    .cw-launcher img { width: 34px; height: 34px; border-radius: 50%; }
    .cw-launcher .cw-x { position: absolute; opacity: 0; transform: rotate(-90deg) scale(0); transition: all 0.3s; }
    .cw-launcher .cw-m { transition: all 0.3s; }
    .cw-launcher.open .cw-m { opacity: 0; transform: rotate(90deg) scale(0); }
    .cw-launcher.open .cw-x { opacity: 1; transform: rotate(0) scale(1); }

    /* Window */
    .cw-win {
      position: absolute; bottom: 72px;
      ${CONFIG.position === 'left' ? 'left: 0;' : 'right: 0;'}
      width: 380px; max-width: calc(100vw - 40px);
      height: 540px; max-height: calc(100vh - 120px);
      background: #fff; border-radius: 12px;
      box-shadow: 0 5px 40px rgba(0,0,0,0.16);
      display: flex; flex-direction: column; overflow: hidden;
      opacity: 0; transform: translateY(12px);
      pointer-events: none;
      transition: opacity 0.2s ease, transform 0.2s ease;
    }
    .cw-win.open { opacity: 1; transform: translateY(0); pointer-events: all; }

    /* Header */
    .cw-hdr {
      background: ${PC}; color: #fff;
      padding: 16px 20px; display: flex; align-items: center; gap: 12px;
    }
    .cw-hdr-icon {
      width: 38px; height: 38px; border-radius: 50%;
      background: rgba(255,255,255,0.2);
      display: flex; align-items: center; justify-content: center;
      flex-shrink: 0;
    }
    .cw-hdr-icon svg { width: 20px; height: 20px; }
    .cw-hdr-icon img { width: 100%; height: 100%; border-radius: 50%; object-fit: cover; }
    .cw-hdr h3 { font-size: 15px; font-weight: 600; }
    .cw-hdr p { font-size: 11px; opacity: 0.9; margin-top: 1px; }
    .cw-dot { display: inline-block; width: 6px; height: 6px; background: #34d399; border-radius: 50%; margin-right: 4px; }

    /* Messages */
    .cw-body {
      flex: 1; overflow-y: auto; padding: 16px;
      background: #eef2f7; display: flex; flex-direction: column; gap: 8px;
    }
    .cw-body::-webkit-scrollbar { width: 4px; }
    .cw-body::-webkit-scrollbar-thumb { background: #c1c9d4; border-radius: 4px; }

    /* Bot row: avatar + bubble */
    .cw-row { display: flex; align-items: flex-end; gap: 8px; max-width: 88%; }
    .cw-row-user { align-self: flex-end; flex-direction: row-reverse; }
    .cw-row-bot { align-self: flex-start; }
    .cw-mini-ava {
      width: 28px; height: 28px; border-radius: 50%;
      background: ${PC}; color: #fff;
      display: flex; align-items: center; justify-content: center;
      flex-shrink: 0;
    }
    .cw-mini-ava svg { width: 14px; height: 14px; }
    .cw-mini-ava img { width: 100%; height: 100%; border-radius: 50%; object-fit: cover; }

    .cw-bub {
      padding: 10px 14px; font-size: 13px; line-height: 1.55;
      word-wrap: break-word; overflow-wrap: anywhere;
      animation: cw-pop 0.15s ease;
    }
    @keyframes cw-pop {
      from { opacity: 0; transform: scale(0.95); }
      to { opacity: 1; transform: scale(1); }
    }
    .cw-bub-bot {
      background: #fff; color: #1e293b;
      border-radius: 2px 16px 16px 16px;
      box-shadow: 0 1px 2px rgba(0,0,0,0.06);
    }
    .cw-bub-user {
      background: ${PC}; color: #fff;
      border-radius: 16px 2px 16px 16px;
    }

    /* Welcome */
    .cw-welcome {
      align-self: flex-start; display: flex; align-items: flex-end; gap: 8px; max-width: 88%;
    }

    /* Typing */
    .cw-typing-row { align-self: flex-start; display: flex; align-items: flex-end; gap: 8px; }
    .cw-dots {
      display: flex; gap: 4px; padding: 12px 16px;
      background: #fff; border-radius: 2px 16px 16px 16px;
      box-shadow: 0 1px 2px rgba(0,0,0,0.06);
    }
    .cw-dots span {
      width: 6px; height: 6px; border-radius: 50%; background: #94a3b8;
      animation: cw-bounce 1.2s ease-in-out infinite;
    }
    .cw-dots span:nth-child(2) { animation-delay: 0.15s; }
    .cw-dots span:nth-child(3) { animation-delay: 0.3s; }
    @keyframes cw-bounce {
      0%,60%,100% { transform: translateY(0); }
      30% { transform: translateY(-4px); }
    }

    /* Quick actions */
    .cw-qa {
      display: flex; flex-wrap: wrap; gap: 6px;
      padding: 6px 16px 10px; background: #eef2f7;
    }
    .cw-qa button {
      padding: 5px 12px; border-radius: 14px;
      border: 1.5px solid ${PC}; background: #fff;
      color: ${PC}; font-size: 12px; font-weight: 500;
      cursor: pointer; font-family: inherit; transition: all 0.15s;
    }
    .cw-qa button:hover { background: ${PC}; color: #fff; }

    /* Input */
    .cw-foot {
      display: flex; align-items: center; gap: 8px;
      padding: 10px 12px; background: #fff; border-top: 1px solid #e5e9ef;
    }
    .cw-foot textarea {
      flex: 1; border: 1px solid #dde2ea; border-radius: 20px;
      padding: 8px 14px; font-size: 13px; font-family: inherit;
      outline: none; resize: none; max-height: 68px;
      color: #334155; background: #f8fafc; line-height: 1.4;
    }
    .cw-foot textarea::placeholder { color: #9ca3af; }
    .cw-foot textarea:focus { border-color: ${PC}; background: #fff; }
    .cw-foot button {
      width: 34px; height: 34px; border-radius: 50%; border: none;
      background: ${PC}; color: #fff; cursor: pointer;
      display: flex; align-items: center; justify-content: center; flex-shrink: 0;
    }
    .cw-foot button:disabled { opacity: 0.35; cursor: default; }
    .cw-foot button svg { width: 15px; height: 15px; }

    /* Branding */
    .cw-brand {
      text-align: center; padding: 5px; font-size: 10px; color: #9ca3af; background: #fff;
    }
    .cw-brand a { color: ${PC}; text-decoration: none; font-weight: 500; }

    @media (max-width: 480px) {
      .cw-win { width: calc(100vw - 16px); height: calc(100vh - 90px); bottom: 70px; border-radius: 10px;
        ${CONFIG.position === 'left' ? 'left: -16px;' : 'right: -16px;'} }
      .cw-launcher { width: 52px; height: 52px; }
    }
  `;

  // --- Quick actions ---
  function qaHTML() {
    if (!CONFIG.quickActions) return '';
    const btns = CONFIG.quickActions.split('|').filter(Boolean)
      .map(a => `<button data-m="${a.trim()}">${a.trim()}</button>`).join('');
    return `<div class="cw-qa" id="cw-qa">${btns}</div>`;
  }

  function brandHTML() {
    if (!CONFIG.footerText) return '';
    const c = CONFIG.footerUrl
      ? `<a href="${CONFIG.footerUrl}" target="_blank">${CONFIG.footerText}</a>`
      : CONFIG.footerText;
    return `<div class="cw-brand">Powered by ${c}</div>`;
  }

  function avaHTML() {
    return `<div class="cw-mini-ava">${getIcon()}</div>`;
  }

  // --- Build ---
  function init() {
    const root = document.createElement('div');
    root.id = WIDGET_ID;
    root.appendChild(styles);
    root.innerHTML += `
      <div class="cw-win" id="cw-win">
        <div class="cw-hdr">
          <div class="cw-hdr-icon">${getIcon()}</div>
          <div>
            <h3>${CONFIG.title}</h3>
            <p><span class="cw-dot"></span>${CONFIG.subtitle}</p>
          </div>
        </div>
        <div class="cw-body" id="cw-body">
          <div class="cw-welcome">
            ${avaHTML()}
            <div class="cw-bub cw-bub-bot">${CONFIG.welcome}</div>
          </div>
        </div>
        ${qaHTML()}
        <div class="cw-foot">
          <textarea id="cw-inp" placeholder="${CONFIG.placeholder}" rows="1"></textarea>
          <button id="cw-snd" disabled>${sendIcon}</button>
        </div>
        ${brandHTML()}
      </div>
      <button class="cw-launcher" id="cw-btn">
        <span class="cw-m">${getIcon()}</span>
        <span class="cw-x">${closeIcon}</span>
      </button>`;
    document.body.appendChild(root);
    wire();
  }

  // --- Events ---
  function wire() {
    const btn = document.getElementById('cw-btn');
    const inp = document.getElementById('cw-inp');
    const snd = document.getElementById('cw-snd');
    const qa = document.getElementById('cw-qa');

    btn.onclick = toggle;
    inp.oninput = () => {
      snd.disabled = !inp.value.trim() || isLoading;
      inp.style.height = 'auto';
      inp.style.height = Math.min(inp.scrollHeight, 68) + 'px';
    };
    inp.onkeydown = e => {
      if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); go(); }
    };
    snd.onclick = go;
    if (qa) qa.onclick = e => {
      const b = e.target.closest('button');
      if (b && !isLoading) { inp.value = b.dataset.m; go(); qa.style.display = 'none'; }
    };
  }

  function toggle() {
    isOpen = !isOpen;
    document.getElementById('cw-win').classList.toggle('open', isOpen);
    document.getElementById('cw-btn').classList.toggle('open', isOpen);
    if (isOpen) document.getElementById('cw-inp').focus();
  }

  function addMsg(text, who) {
    const body = document.getElementById('cw-body');
    const row = document.createElement('div');
    row.className = `cw-row cw-row-${who}`;
    if (who === 'bot') row.innerHTML = avaHTML();
    const bub = document.createElement('div');
    bub.className = `cw-bub cw-bub-${who}`;
    bub.textContent = who === 'bot' ? stripMarkdown(text) : text;
    row.appendChild(bub);
    body.appendChild(row);
    body.scrollTop = body.scrollHeight;
  }

  function showDots() {
    const body = document.getElementById('cw-body');
    const row = document.createElement('div');
    row.className = 'cw-typing-row'; row.id = 'cw-typ';
    row.innerHTML = `${avaHTML()}<div class="cw-dots"><span></span><span></span><span></span></div>`;
    body.appendChild(row); body.scrollTop = body.scrollHeight;
  }
  function hideDots() { document.getElementById('cw-typ')?.remove(); }

  function lock(v) {
    isLoading = v;
    const inp = document.getElementById('cw-inp');
    document.getElementById('cw-snd').disabled = v || !inp.value.trim();
    inp.disabled = v;
  }

  async function go() {
    const inp = document.getElementById('cw-inp');
    const text = inp.value.trim(); if (!text) return;
    inp.value = ''; inp.style.height = 'auto';
    addMsg(text, 'user'); lock(true); showDots();
    try {
      const r = await fetch(`${CONFIG.apiUrl}/api/v1/ask`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-API-Key': CONFIG.apiKey },
        body: JSON.stringify({ user_id: 'widget-user', session_id: sessionId, message: text }),
      });
      if (!r.ok) throw new Error(r.status);
      await poll((await r.json()).run_id);
    } catch {
      hideDots(); addMsg("Sorry, I'm having trouble connecting. Please try again.", 'bot');
    } finally { lock(false); }
  }

  async function poll(id) {
    for (let i = 0; i < MAX_POLLS; i++) {
      await new Promise(r => setTimeout(r, POLL_INTERVAL));
      try {
        const r = await fetch(`${CONFIG.apiUrl}/api/v1/runs/${id}`, { headers: { 'X-API-Key': CONFIG.apiKey } });
        if (!r.ok) continue;
        const d = await r.json();
        if (d.status === 'done') { hideDots(); addMsg(d.answer || 'No response.', 'bot'); return; }
        if (d.status === 'failed') { hideDots(); addMsg(d.error || 'Something went wrong.', 'bot'); return; }
      } catch { continue; }
    }
    hideDots(); addMsg('Response took too long.', 'bot');
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
