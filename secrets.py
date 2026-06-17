"""
pass-cli secret retrieval for discord-bot2.

Secrets are stored in the "APIs" vault as individual items.
Fetched with:
    pass-cli item view --vault-name APIs --item-title <item> --field "API Key"
"""

import subprocess
import logging

log = logging.getLogger("secrets")

VAULT = "APIs"

_FIELDS = {
    "DISCORD_TOKEN": "Bot2- Discord Token",
    "DEEPL_API_KEY": "Bot2 - DeepL API Key",
}


def get_secret(field: str) -> str:
    """Fetch the API Key field from a named pass-cli item. Raises on failure."""
    item = _FIELDS[field]
    try:
        result = subprocess.run(
            ["pass-cli", "item", "view", "--vault-name", VAULT, "--item-title", item, "--field", "API Key"],
            capture_output=True,
            text=True,
            check=True,
        )
        value = result.stdout.strip()
        if not value:
            raise ValueError(f"pass-cli returned empty value for '{item}'")
        return value
    except subprocess.CalledProcessError as e:
        raise RuntimeError(
            f"pass-cli failed for '{item}': {e.stderr.strip()}"
        ) from e


def load_secrets() -> dict[str, str]:
    """Load all required secrets from pass-cli. Raises if any are missing."""
    secrets: dict[str, str] = {}
    errors: list[str] = []

    for field in _FIELDS:
        try:
            secrets[field] = get_secret(field)
            log.info(f"Loaded secret: {field}")
        except (RuntimeError, ValueError) as e:
            errors.append(str(e))
            log.error(e)

    if errors:
        raise RuntimeError(
            "Failed to load one or more secrets from pass-cli:\n" + "\n".join(errors)
        )

    return secrets
