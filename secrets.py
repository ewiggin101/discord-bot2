"""
Proton Pass secret retrieval for discord-bot2.

Secrets are stored in Proton Pass vault "APIs" as individual items.
Fetched with:
    proton-pass item get --vault APIs --name <item> --field password
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
    """Fetch the password field from a named Proton Pass item. Raises on failure."""
    item = _FIELDS[field]
    try:
        result = subprocess.run(
            ["proton-pass", "item", "get", "--vault", VAULT, "--name", item, "--field", "password"],
            capture_output=True,
            text=True,
            check=True,
        )
        value = result.stdout.strip()
        if not value:
            raise ValueError(f"Proton Pass returned empty value for '{item}'")
        return value
    except subprocess.CalledProcessError as e:
        raise RuntimeError(
            f"proton-pass failed for '{item}': {e.stderr.strip()}"
        ) from e


def load_secrets() -> dict[str, str]:
    """Load all required secrets from Proton Pass. Raises if any are missing."""
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
            "Failed to load one or more secrets from Proton Pass:\n" + "\n".join(errors)
        )

    return secrets
