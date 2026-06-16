"""
Translation Service — all languages handled by DeepL.
"""

import asyncio
import logging
import deepl
from config import Config

log = logging.getLogger("TranslationService")


class TranslationService:

    def __init__(self, deepl_api_key: str):
        self.deepl_client = deepl.Translator(deepl_api_key)

    # ── Public API ────────────────────────────────────────────────────────────

    async def translate(self, text: str, source_lang: str, target_lang: str) -> str | None:
        """Translate text via DeepL. Returns translated string, or None on failure."""
        if not text or not text.strip():
            return None

        text = text[:Config.MAX_MESSAGE_LENGTH]

        try:
            async with asyncio.timeout(Config.TRANSLATION_TIMEOUT):
                return await self._deepl_translate(text, source_lang, target_lang)
        except asyncio.TimeoutError:
            log.error(f"Translation timed out ({source_lang}→{target_lang})")
            return None

    # ── DeepL ─────────────────────────────────────────────────────────────────

    async def _deepl_translate(self, text: str, source_lang: str, target_lang: str) -> str | None:
        if not self.deepl_client:
            log.error("DeepL client not initialized")
            return None

        try:
            deepl_target = Config.DEEPL_LANG_CODES.get(target_lang, target_lang.upper())
            deepl_source = Config.DEEPL_SOURCE_LANG_CODES.get(source_lang, source_lang.upper())

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
