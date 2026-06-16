# 🌐 Discord Multi-Language Translation Bot

Automatically translates messages across language-specific channels in real time.

**Supported languages:** English · Korean · Spanish · French · Portuguese

**Translation engine:** [DeepL](https://www.deepl.com/pro-api) — all language pairs

---

## 📁 File Structure

```
discord-translator-bot/
├── bot.py               # Main bot — Discord client, events, commands
├── translator.py        # Translation service (DeepL)
├── channel_manager.py   # Channel registry with JSON persistence
├── config.py            # Languages, colors, channel keywords
├── requirements.txt     # Python dependencies
├── .env.example         # Environment variable template
└── channel_registry.json  # Auto-created on first !tsetup
```

---

## ⚙️ Setup

### 1. Prerequisites

- Python 3.11+
- A Discord bot application with these intents enabled:
  - `Message Content Intent`
  - `Server Members Intent`
  - `Presence Intent`

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Get Your API Keys

| Key | Where to Get It | Free Tier |
|-----|----------------|-----------|
| `DISCORD_TOKEN` | [discord.com/developers](https://discord.com/developers/applications) | Free |
| `DEEPL_API_KEY` | [deepl.com/pro-api](https://www.deepl.com/pro-api) | 500K chars/month |

### 4. Configure Environment

```bash
cp .env.example .env
# Edit .env and fill in your keys
```

### 5. Run the Bot

```bash
python bot.py
```

---

## 🏗️ Discord Server Structure

Create your channels following this naming convention
(or use `!tregister` to manually register any name):

```
📁 CATEGORY: 🇺🇸 English
   📢 en-announcements
   💬 en-general

📁 CATEGORY: 🇰🇷 Korean
   📢 ko-announcements
   💬 ko-general

📁 CATEGORY: 🇪🇸 Spanish
   📢 es-announcements
   💬 es-general

📁 CATEGORY: 🇫🇷 French
   📢 fr-announcements
   💬 fr-general

📁 CATEGORY: 🇧🇷 Portuguese
   📢 pt-announcements
   💬 pt-general

📁 CATEGORY: 🔧 Server
   📋 pick-your-language   ← Carl-bot reaction roles go here
   📢 rules
   💬 lobby
```

### Required Bot Permissions

In each translation channel, the bot needs:
- `Read Messages`
- `Send Messages`
- `Manage Webhooks`
- `Embed Links`
- `Read Message History`

---

## 🤖 Carl-bot Reaction Roles (Language Gating)

Use **Carl-bot** (free) to let users self-assign language roles via emoji reactions.

### Step 1 — Create Roles in Discord

Create one role per language:
- `🇺🇸 English Speaker`
- `🇰🇷 Korean Speaker`
- `🇪🇸 Spanish Speaker`
- `🇫🇷 French Speaker`
- `🇧🇷 Portuguese Speaker`

### Step 2 — Set Channel Permissions

For each language category, configure permissions so **only that role** can view it:

```
Category: 🇰🇷 Korean
  @everyone          → View Channel: ❌ DENY
  🇰🇷 Korean Speaker → View Channel: ✅ ALLOW
  TranslatorBot      → View Channel: ✅ ALLOW (always)
```

Repeat for each language category.

### Step 3 — Set Up Carl-bot Reaction Roles

In `#pick-your-language`, run this Carl-bot command:

```
!reactionrole create "Pick your language to unlock your channels!" exclusive
!reactionrole add 🇺🇸 "English Speaker"
!reactionrole add 🇰🇷 "Korean Speaker"
!reactionrole add 🇪🇸 "Spanish Speaker"
!reactionrole add 🇫🇷 "French Speaker"
!reactionrole add 🇧🇷 "Portuguese Speaker"
```

The `exclusive` flag means users can only pick one language role at a time.
Remove it if you want users to access multiple language channels.

---

## 🛠️ Bot Commands

| Command | Description | Who |
|---------|-------------|-----|
| `!tsetup` | Auto-detect & register all language channels | Admin |
| `!tregister <lang> <type>` | Manually register current channel | Admin |
| `!tunregister` | Remove current channel from translation | Admin |
| `!tstatus` | Show all registered channels | Admin |
| `!ttest <lang> <text>` | Test translation to a language | Admin |
| `!thelp` | Show command list | Anyone |

### Examples

```
!tsetup                          # Auto-register all matching channels
!tregister ko general            # Register current channel as Korean general
!tregister fr announcements      # Register current channel as French announcements
!ttest ko Hello everyone!        # Test Korean translation
!tstatus                         # View channel map
```

---

## 📊 How Translation Works

```
User types in #en-general
         │
         ▼
  Bot detects message
         │
         ▼
  Identify source lang (en)
         │
         ▼
  For each other language:
    ├─ Korean? ──────► DeepL API ───► Post to #ko-general
    ├─ Spanish? ─────► DeepL API ───► Post to #es-general
    ├─ French? ──────► DeepL API ───► Post to #fr-general
    └─ Portuguese? ──► DeepL API ───► Post to #pt-general
         │
         ▼
  Messages appear as webhooks
  (show original author name + avatar)
```

All translations run **concurrently** — no sequential delays.

---

## ➕ Adding a New Language

1. Add to `config.py`:

```python
LANGUAGE_NAMES = {
    ...
    "ja": "Japanese",
}

LANGUAGE_FLAGS = {
    ...
    "ja": "🇯🇵",
}

DEEPL_LANG_CODES = {
    ...
    "ja": "JA",
}

CHANNEL_KEYWORDS = {
    ...
    "ja": {
        "general":       ["ja-general", "japanese-general"],
        "announcements": ["ja-announcements", "japanese-announce"],
    }
}
```

2. Create the Discord channels and category
3. Run `!tsetup` — done.

---

## 🚀 Deployment (Production)

### Railway.app (Recommended — ~$5/month)

```bash
# Install Railway CLI
npm install -g @railway/cli

railway login
railway init
railway up
```

Set your environment variables in the Railway dashboard under **Variables**.

### Systemd (Self-hosted Linux server)

```ini
# /etc/systemd/system/translator-bot.service
[Unit]
Description=Discord Translator Bot
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/opt/discord-translator-bot
ExecStart=/usr/bin/python3 bot.py
Restart=always
RestartSec=10
EnvironmentFile=/opt/discord-translator-bot/.env

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable translator-bot
sudo systemctl start translator-bot
sudo journalctl -u translator-bot -f   # View logs
```

---

## 🐛 Troubleshooting

| Issue | Fix |
|-------|-----|
| Bot online but not translating | Run `!tstatus` — channels may not be registered. Run `!tsetup`. |
| Messages appear as bot, not user | Bot needs `Manage Webhooks` permission in the channel. |
| Translations failing | Check `DEEPL_API_KEY` in `.env`. Verify free tier hasn't been exhausted. |
| Channels not auto-detected | Channel names must match patterns in `config.py → CHANNEL_KEYWORDS`. Use `!tregister` to register manually. |
| Translation loop | Bot ignores all messages from bots — should not occur. Check bot role has `bot` tag. |
