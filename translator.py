"""
Translation Service
- Korean <-> Any  : Papago (Naver) — best-in-class Korean accuracy
- All other pairs : DeepL          — best for ES, FR, PT

To swap or add a backend later, add a new method (e.g. google_translate)
and update the route() logic in translate(). Nothing else needs to change.
"""

import os
import asyncio
import logging
import aiohttp
import deepl
from config import Config

log = logging.getLogger("TranslationService")


class TranslationService:

    def __init__(self):
        # DeepL async client
        self.deepl_key = os.getenv("DEEPL_API_KEY")
        self.deepl_client = deepl.Translator(self.deepl_key) if self.deepl_key else None

        # Papago credentials (Naver Cloud Platform)
        self.papago_client_id = os.getenv("PAPAGO_CLIENT_ID")
        self.papago_client_secret = os.getenv("PAPAGO_CLIENT_SECRET")

        if not self.deepl_key:
            log.warning("DEEPL_API_KEY not set — DeepL translations will fail")
        if not self.papago_client_id or not self.papago_client_secret:
            log.warning("PAPAGO credentials not set — Korean translations will fail")

    # ── Public API ────────────────────────────────────────────────────────────

    async def translate(self, text: str, source_lang: str, target_lang: str) -> str | None:
        """
        Route the translation to the best engine for this language pair.
        Returns the translated string, or None on failure.
        """
        if not text or not text.strip():
            return None

        # Trim to Discord-safe length
        text = text[:Config.MAX_MESSAGE_LENGTH]

        try:
            async with asyncio.timeout(Config.TRANSLATION_TIMEOUT):
                return await self._route(text, source_lang, target_lang)
        except asyncio.TimeoutError:
            log.error(f"Translation timed out ({source_lang}→{target_lang})")
            return None

    # ── Routing Logic ─────────────────────────────────────────────────────────

    async def _route(self, text: str, source_lang: str, target_lang: str) -> str | None:
        """
        Decision tree:
          Korean involved  → Papago
          Everything else  → DeepL

        To add DeepL as a fallback for Korean if Papago is down,
        just add an `except` clause that calls self._deepl_translate().
        """
        if source_lang in Config.PAPAGO_LANGUAGES or target_lang in Config.PAPAGO_LANGUAGES:
            return await self._papago_translate(text, source_lang, target_lang)
        else:
            return await self._deepl_translate(text, source_lang, target_lang)

    # ── DeepL ─────────────────────────────────────────────────────────────────

    async def _deepl_translate(self, text: str, source_lang: str, target_lang: str) -> str | None:
        """
        Translate using the DeepL API.
        DeepL uses its own language codes (e.g. EN-US, PT-BR) — mapped in config.
        """
        if not self.deepl_client:
            log.error("DeepL client not initialized")
            return None

        try:
            deepl_target = Config.DEEPL_LANG_CODES.get(target_lang, target_lang.upper())
            deepl_source = Config.DEEPL_LANG_CODES.get(source_lang, source_lang.upper())

            # Run DeepL (sync SDK) in a thread so we don't block the event loop
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: self.deepl_client.translate_text(
                    text,
                    source_lang=deepl_source,
                    target_lang=deepl_target
                )
            )
            return str(result)

        except deepl.DeepLException as e:
            log.error(f"DeepL error ({source_lang}→{target_lang}): {e}")
            return None

    # ── Papago ────────────────────────────────────────────────────────────────

    async def _papago_translate(self, text: str, source_lang: str, target_lang: str) -> str | None:
        """
        Translate using Naver's Papago API (Naver Cloud Platform).
        Free tier: 10,000 characters/day.
        Register at: https://www.ncloud.com/
        """
        if not self.papago_client_id or not self.papago_client_secret:
            log.error("Papago credentials not set")
            return None

        papago_source = Config.PAPAGO_LANG_CODES.get(source_lang, source_lang)
        papago_target = Config.PAPAGO_LANG_CODES.get(target_lang, target_lang)

        url = "https://naveropenapi.apigw.ntruss.com/nmt/v1/translation"
        headers = {
            "X-NCP-APIGW-API-KEY-ID": self.papago_client_id,
            "X-NCP-APIGW-API-KEY":    self.papago_client_secret,
            "Content-Type":           "application/x-www-form-urlencoded",
        }
        data = {
            "source": papago_source,
            "target": papago_target,
            "text":   text,
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, data=data) as resp:
                    if resp.status != 200:
                        error_body = await resp.text()
                        log.error(f"Papago HTTP {resp.status}: {error_body}")
                        return None

                    json_data = await resp.json()
                    return json_data["message"]["result"]["translatedText"]

        except aiohttp.ClientError as e:
            log.error(f"Papago network error ({source_lang}→{target_lang}): {e}")
            return None
        except (KeyError, ValueError) as e:
            log.error(f"Papago response parse error: {e}")
            return None
