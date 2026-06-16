"""
Channel Manager
Tracks which Discord channels are registered for translation,
what language they carry, and what type (general / announcements).

Storage is in-memory with JSON persistence so registrations
survive bot restarts without needing a database.
"""

import json
import logging
import os
from typing import Dict, Optional
from config import Config

log = logging.getLogger("ChannelManager")

PERSISTENCE_FILE = "channel_registry.json"


class ChannelManager:

    def __init__(self):
        # Structure:
        # {
        #   channel_id (int): {
        #     "guild_id": int,
        #     "lang": str,       # "en" | "ko" | "es" | "fr" | "pt"
        #     "type": str        # "general" | "announcements"
        #   }
        # }
        self._registry: Dict[int, dict] = {}
        self._load()

    # ── Registration ──────────────────────────────────────────────────────────

    def register_channel(
        self,
        guild_id: int,
        channel_id: int,
        lang: str,
        channel_type: str
    ):
        """Register a channel for translation routing."""
        self._registry[channel_id] = {
            "guild_id": guild_id,
            "lang": lang,
            "type": channel_type,
        }
        self._save()
        log.info(f"Registered channel {channel_id} as {lang}/{channel_type} in guild {guild_id}")

    def unregister_channel(self, channel_id: int) -> bool:
        """Remove a channel from translation routing. Returns True if it existed."""
        if channel_id in self._registry:
            del self._registry[channel_id]
            self._save()
            return True
        return False

    # ── Lookups ───────────────────────────────────────────────────────────────

    def get_channel_info(self, channel_id: int) -> Optional[dict]:
        """Return registration info for a channel, or None if not registered."""
        return self._registry.get(channel_id)

    def get_target_channels(
        self,
        guild_id: int,
        source_lang: str,
        channel_type: str
    ) -> Dict[str, int]:
        """
        Return all channels in this guild of the same type but different language.
        Format: { "ko": 123456789, "es": 987654321, ... }
        """
        targets = {}
        for ch_id, info in self._registry.items():
            if (
                info["guild_id"] == guild_id
                and info["type"] == channel_type
                and info["lang"] != source_lang
                and info["lang"] in Config.ACTIVE_LANGUAGES
            ):
                targets[info["lang"]] = ch_id
        return targets

    def get_guild_channels(self, guild_id: int) -> Dict[int, dict]:
        """Return all registered channels for a guild."""
        return {
            ch_id: info
            for ch_id, info in self._registry.items()
            if info["guild_id"] == guild_id
        }

    # ── Persistence ───────────────────────────────────────────────────────────

    def _save(self):
        """Write registry to disk (int keys → str for JSON)."""
        try:
            serializable = {str(k): v for k, v in self._registry.items()}
            with open(PERSISTENCE_FILE, "w") as f:
                json.dump(serializable, f, indent=2)
        except OSError as e:
            log.error(f"Failed to save channel registry: {e}")

    def _load(self):
        """Load registry from disk on startup."""
        if not os.path.exists(PERSISTENCE_FILE):
            log.info("No channel registry found — starting fresh")
            return
        try:
            with open(PERSISTENCE_FILE) as f:
                raw = json.load(f)
            # JSON keys are always strings; convert back to int
            self._registry = {int(k): v for k, v in raw.items()}
            log.info(f"Loaded {len(self._registry)} channel(s) from registry")
        except (OSError, json.JSONDecodeError) as e:
            log.error(f"Failed to load channel registry: {e}")
            self._registry = {}
