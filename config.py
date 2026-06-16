"""
Bot configuration — languages, colors, channel naming conventions.
Edit this file to add new languages or change channel naming patterns.
"""

class Config:

    # ── Supported Languages ───────────────────────────────────────────────────
    # Add new languages here — the rest of the bot picks them up automatically
    LANGUAGE_NAMES = {
        "en": "English",
        "ko": "Korean",
        "es": "Spanish",
        "fr": "French",
        "pt": "Portuguese",
    }

    LANGUAGE_FLAGS = {
        "en": "🇺🇸",
        "ko": "🇰🇷",
        "es": "🇪🇸",
        "fr": "🇫🇷",
        "pt": "🇧🇷",
    }

    # Embed accent colors per language
    LANGUAGE_COLORS = {
        "en": 0x3498DB,   # Blue
        "ko": "0xCD2E3A", # Korean red
        "es": 0xF1C40F,   # Spanish yellow
        "fr": 0x002395,   # French blue
        "pt": 0x009C3B,   # Portuguese green
    }

    # ── Translation Routing ───────────────────────────────────────────────────
    # All languages route through DeepL.

    # DeepL language codes (some differ from ISO 639-1)
    DEEPL_LANG_CODES = {
        "en": "EN-US",
        "ko": "KO",
        "es": "ES",
        "fr": "FR",
        "pt": "PT-BR",   # Change to PT-PT for European Portuguese if needed
    }

    # ── Channel Auto-Detection Keywords ──────────────────────────────────────
    # Used by !tsetup to auto-register channels by name pattern.
    # Channels matching ANY keyword in the list will be registered.
    CHANNEL_KEYWORDS = {
        "en": {
            "general":       ["en-general", "english-general", "en-chat", "english-chat"],
            "announcements": ["en-announce", "en-announcements", "english-announce"],
        },
        "ko": {
            "general":       ["ko-general", "korean-general", "ko-chat", "korean-chat"],
            "announcements": ["ko-announce", "ko-announcements", "korean-announce"],
        },
        "es": {
            "general":       ["es-general", "spanish-general", "es-chat", "espanol-general"],
            "announcements": ["es-announce", "es-announcements", "spanish-announce"],
        },
        "fr": {
            "general":       ["fr-general", "french-general", "fr-chat", "francais-general"],
            "announcements": ["fr-announce", "fr-announcements", "french-announce"],
        },
        "pt": {
            "general":       ["pt-general", "portuguese-general", "pt-chat", "portugues-general"],
            "announcements": ["pt-announce", "pt-announcements", "portuguese-announce"],
        },
    }

    # ── Active Languages ─────────────────────────────────────────────────────
    # Remove a code from this set to disable that language without touching
    # any other code. The bot will ignore channels registered for that language.
    ACTIVE_LANGUAGES = {"en", "ko", "es"} # "fr" "pt" disabled

    # ── Bot Settings ──────────────────────────────────────────────────────────
    MAX_MESSAGE_LENGTH = 1900   # Discord limit is 2000; leave headroom for embed
    TRANSLATION_TIMEOUT = 10    # Seconds before a translation API call times out
