# Nalla — Reference Domain Agent

Nalla is the reference domain this framework ships with: a chat assistant that answers questions about what foods are safe for dogs. It's wired end-to-end so you can run it locally, visually verify the widget, and use it as a blueprint for your own domain.

## What's Included

- **System prompt** — `seeds/prompts.json` (tone + safety rails for dog-food questions)
- **Router config** — `router_config.json` (keyword rules + default agent)
- **Env example** — `nalla.env.example` (persona name, guardrail patterns)
- **Widget demo** — `/widget/demo.html` at the repo root, pre-branded for [Dog Food & Fun](https://dogfoodandfun.com)

## Branding (Dog Food & Fun)

| Token | Value |
|---|---|
| Primary | `#ff5f42` (coral) |
| Text | `#3a3a3a` |
| Background | `#FBFCFF` |
| Font | [Poppins](https://fonts.google.com/specimen/Poppins) |
| Launcher icon | `/widget/paw-white.svg` |
| Title + bot avatar | `/widget/paw-coral.svg` |

## Widget Snippet (Production Drop-in)

```html
<script type="module">
  import Chatbot from 'https://cdn.jsdelivr.net/npm/flowise-embed/dist/web.js';
  Chatbot.init({
    chatflowid: 'nalla',
    apiHost: 'https://api.yourdomain.com',
    chatflowConfig: {
      uploads: {
        isImageUploadAllowed: true,
        imgUploadSizeAndTypes: [
          { fileTypes: ['image/jpeg', 'image/png', 'image/webp'], maxSizeMB: 5 },
        ],
      },
    },
    theme: {
      button: {
        backgroundColor: '#ff5f42',
        customIconSrc: '/widget/paw-white.svg',
      },
      chatWindow: {
        title: "Nalla's Dad",
        titleAvatarSrc: '/widget/paw-coral.svg',
        welcomeMessage: 'Hey! Ask me if any food is safe for your dog.',
        backgroundColor: '#FBFCFF',
        botMessage: {
          backgroundColor: '#ffffff',
          textColor: '#3a3a3a',
          avatarSrc: '/widget/paw-coral.svg',
        },
        userMessage: { backgroundColor: '#ff5f42', textColor: '#ffffff' },
        textInput: {
          placeholder: 'Ask about any food...',
          sendButtonColor: '#ff5f42',
        },
      },
    },
  });
</script>
```

## Deployment Env Vars

```env
AGENT_NAME=nalla
PERSONA_NAME=Nalla's Dad
LLM_PROVIDER=gemini
LLM_MODEL=gemini-2.5-flash
REDIS_KEY_PREFIX=nalla
INJECTION_PATTERNS=["ignore previous instructions","forget your rules","jailbreak"]
FORBIDDEN_OUTPUT_PATTERNS=["diagnose","prescribe","treatment plan"]
WIDGET_ALLOWED_ORIGINS=["https://dogfoodandfun.com"]
```

## Using This as a Template

Copy this folder to `agents/<your-name>/` and swap:
1. `seeds/prompts.json` — your domain-specific system prompt
2. `router_config.json` — your keyword routing rules
3. `<your-name>.env.example` — your persona, guardrails, LLM choice
4. Widget branding in `widget/demo.html` — your colors, icons, copy

See [`CONTRIBUTING.md`](../../CONTRIBUTING.md#adding-a-new-domain-agent) for the full domain-onboarding checklist.
