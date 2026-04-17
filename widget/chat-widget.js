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
  const clipIcon = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"/></svg>';
  const removeIcon = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>';
  let pendingImage = null;

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
      flex: 1; overflow-y: auto; padding: 20px;
      background: #eef2f7; display: flex; flex-direction: column; gap: 12px;
    }
    .cw-body::-webkit-scrollbar { width: 4px; }
    .cw-body::-webkit-scrollbar-thumb { background: #c1c9d4; border-radius: 4px; }

    /* Bot row: avatar + bubble */
    .cw-row { display: flex; align-items: flex-end; gap: 8px; max-width: 82%; }
    .cw-row-user { align-self: flex-end; flex-direction: row-reverse; }
    .cw-row-bot { align-self: flex-start; }
    .cw-welcome { max-width: 82%; }
    .cw-mini-ava {
      width: 28px; height: 28px; border-radius: 50%;
      background: ${PC}; color: #fff;
      display: flex; align-items: center; justify-content: center;
      flex-shrink: 0;
    }
    .cw-mini-ava svg { width: 14px; height: 14px; }
    .cw-mini-ava img { width: 100%; height: 100%; border-radius: 50%; object-fit: cover; }

    .cw-bub {
      padding: 12px 18px; font-size: 14px; line-height: 1.6;
      word-wrap: break-word; overflow-wrap: anywhere;
      animation: cw-pop 0.15s ease;
      direction: auto; unicode-bidi: plaintext;
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
      align-self: flex-start; display: flex; align-items: flex-end; gap: 8px;
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
      display: flex; flex-wrap: wrap; gap: 8px;
      padding: 10px 20px 14px; background: #eef2f7;
    }
    .cw-qa button {
      padding: 8px 18px; border-radius: 18px;
      border: 1.5px solid ${PC}; background: #fff;
      color: ${PC}; font-size: 12px; font-weight: 500;
      cursor: pointer; font-family: inherit; transition: all 0.15s;
    }
    .cw-qa button:hover { background: ${PC}; color: #fff; }

    /* Image preview */
    .cw-img-preview {
      padding: 8px 12px 0; background: #fff; display: none;
    }
    .cw-img-preview.active { display: flex; align-items: center; gap: 8px; }
    .cw-img-preview img {
      width: 48px; height: 48px; border-radius: 8px; object-fit: cover;
      border: 1px solid #e5e9ef;
    }
    .cw-img-preview .cw-img-name {
      flex: 1; font-size: 11px; color: #64748b;
      overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
    }
    .cw-img-preview button {
      width: 22px; height: 22px; border-radius: 50%; border: none;
      background: #ef4444; color: #fff; cursor: pointer;
      display: flex; align-items: center; justify-content: center; flex-shrink: 0;
    }
    .cw-img-preview button svg { width: 14px; height: 14px; }

    /* Bubble image */
    .cw-bub img.cw-chat-img {
      max-width: 100%; border-radius: 8px; margin-top: 6px; display: block;
    }

    /* Input */
    .cw-foot {
      display: flex; align-items: center; gap: 8px;
      padding: 12px 20px; background: #fff; border-top: 1px solid #e5e9ef;
    }
    .cw-clip {
      width: 34px; height: 34px; border-radius: 50%; border: none;
      background: transparent; color: #94a3b8; cursor: pointer;
      display: flex; align-items: center; justify-content: center; flex-shrink: 0;
      transition: color 0.15s;
    }
    .cw-clip:hover { color: ${PC}; }
    .cw-clip svg { width: 18px; height: 18px; }
    .cw-clip input { display: none; }
    .cw-foot textarea {
      flex: 1; border: 1px solid #dde2ea; border-radius: 22px;
      padding: 10px 18px; font-size: 14px; font-family: inherit;
      outline: none; resize: none; max-height: 68px;
      color: #334155; background: #f8fafc; line-height: 1.4;
    }
    .cw-foot textarea::placeholder { color: #9ca3af; }
    .cw-foot textarea:focus { border-color: ${PC}; background: #fff; }
    .cw-snd {
      width: 34px; height: 34px; border-radius: 50%; border: none;
      background: ${PC}; color: #fff; cursor: pointer;
      display: flex; align-items: center; justify-content: center; flex-shrink: 0;
    }
    .cw-snd:disabled { opacity: 0.35; cursor: default; }
    .cw-snd svg { width: 15px; height: 15px; }

    /* Branding */
    .cw-brand {
      text-align: center; padding: 5px; font-size: 10px; color: #9ca3af; background: #fff;
    }
    .cw-brand a { color: ${PC}; text-decoration: none; font-weight: 500; }

    @media (max-width: 480px) {
      #${WIDGET_ID} { bottom: 16px; ${CONFIG.position === 'left' ? 'left: 16px;' : 'right: 16px;'} }
      .cw-win {
        position: fixed; top: 0; left: 0; right: 0; bottom: 0;
        width: 100%; height: 100%; max-width: 100%; max-height: 100%;
        border-radius: 0; z-index: 1000000;
      }
      .cw-launcher { width: 52px; height: 52px; }
      .cw-launcher svg { width: 22px; height: 22px; }
      .cw-hdr { padding: 14px 16px; padding-top: max(14px, env(safe-area-inset-top)); }
      .cw-foot { padding-bottom: max(10px, env(safe-area-inset-bottom)); }
      .cw-bub { font-size: 14px; }
      .cw-qa button { font-size: 13px; padding: 7px 14px; }
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
        <div class="cw-img-preview" id="cw-img-preview">
          <img id="cw-img-thumb" src="" alt="">
          <span class="cw-img-name" id="cw-img-name"></span>
          <button id="cw-img-rm">${removeIcon}</button>
        </div>
        <div class="cw-foot">
          <label class="cw-clip" title="Attach image">
            ${clipIcon}
            <input type="file" id="cw-file" accept="image/*">
          </label>
          <textarea id="cw-inp" dir="auto" placeholder="${CONFIG.placeholder}" rows="1"></textarea>
          <button class="cw-snd" id="cw-snd" disabled>${sendIcon}</button>
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
    const file = document.getElementById('cw-file');
    const imgRm = document.getElementById('cw-img-rm');

    btn.onclick = toggle;
    inp.oninput = () => {
      snd.disabled = (!inp.value.trim() && !pendingImage) || isLoading;
      inp.style.height = 'auto';
      inp.style.height = Math.min(inp.scrollHeight, 68) + 'px';
    };
    inp.onkeydown = e => {
      if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); go(); }
    };
    snd.onclick = go;

    file.onchange = e => {
      const f = e.target.files?.[0];
      if (!f || !f.type.startsWith('image/')) return;
      const reader = new FileReader();
      reader.onload = () => {
        pendingImage = { dataUrl: reader.result, name: f.name };
        document.getElementById('cw-img-thumb').src = reader.result;
        document.getElementById('cw-img-name').textContent = f.name;
        document.getElementById('cw-img-preview').classList.add('active');
        document.getElementById('cw-snd').disabled = false;
      };
      reader.readAsDataURL(f);
      file.value = '';
    };

    imgRm.onclick = () => {
      pendingImage = null;
      document.getElementById('cw-img-preview').classList.remove('active');
      snd.disabled = !inp.value.trim() || isLoading;
    };

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

  function addMsg(text, who, imageUrl) {
    const body = document.getElementById('cw-body');
    const row = document.createElement('div');
    row.className = `cw-row cw-row-${who}`;
    if (who === 'bot') row.innerHTML = avaHTML();
    const bub = document.createElement('div');
    bub.className = `cw-bub cw-bub-${who}`;
    bub.setAttribute('dir', 'auto');
    if (imageUrl) {
      const img = document.createElement('img');
      img.src = imageUrl;
      img.className = 'cw-chat-img';
      img.alt = 'Uploaded image';
      bub.appendChild(img);
    }
    if (text) {
      const span = document.createElement('span');
      span.textContent = who === 'bot' ? stripMarkdown(text) : text;
      bub.appendChild(span);
    }
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
    const text = inp.value.trim();
    const img = pendingImage;
    if (!text && !img) return;
    inp.value = ''; inp.style.height = 'auto';
    addMsg(text || '(image)', 'user', img?.dataUrl);
    pendingImage = null;
    document.getElementById('cw-img-preview').classList.remove('active');
    lock(true); showDots();
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
