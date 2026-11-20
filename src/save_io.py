"""Read and write the individual game files in the PRD text formats."""

import re

from save_paths import COINS_PATH, GUNS_PATH, UPGRADE_PATH
from shop import MAX_UPGRADE_LEVEL


class SaveDataError(ValueError):
    """Raised when a game file cannot be parsed into valid save data."""


def _read_text(path):
    try:
        return path.read_text(encoding="utf-8")
    except OSError as error:
        raise SaveDataError("cannot read {}: {}".format(path, error)) from error


def _write_text(path, text):
    try:
        path.write_text(text + "\n", encoding="utf-8")
    except OSError as error:
        raise SaveDataError("cannot write {}: {}".format(path, error)) from error


def _parse_list(text, key):
    match = re.fullmatch(
        r"\s*{}\s*=\s*\[(.*)\]\s*".format(re.escape(key)),
        text,
        flags=re.DOTALL,
    )
    if match is None:
        raise SaveDataError("invalid {} format".format(key))
    return [item.strip() for item in match.group(1).split(",") if item.strip()]


def _format_list(key, values):
    return "{} = [{}]".format(key, ", ".join(str(value) for value in values))


def write_guns(acquired_guns, path=None):
    """Write the owned-gun flags to getGuns.txt."""
    values = ["true" if owned else "false" for owned in acquired_guns]
    _write_text(path or GUNS_PATH, _format_list("acquire", values))


def read_guns(path=None):
    """Read the owned-gun flags from getGuns.txt."""
    values = _parse_list(_read_text(path or GUNS_PATH), "acquire")
    flags = []
    for value in values:
        lowered = value.lower()
        if lowered not in ("true", "false"):
            raise SaveDataError("invalid gun ownership value: {}".format(value))
        flags.append(lowered == "true")
    return flags


def _parse_int(value, label):
    try:
        return int(value)
    except (TypeError, ValueError) as error:
        raise SaveDataError("invalid {} value: {}".format(label, value)) from error


def write_upgrade_levels(upgrade_levels, path=None):
    """Write internal 0-based levels as the PRD's 1-based gunLevel values."""
    stored_levels = []
    for level in upgrade_levels:
        internal_level = _parse_int(level, "gun level")
        if internal_level < 0 or internal_level > MAX_UPGRADE_LEVEL:
            raise SaveDataError(
                "gun level must be between 0 and {}: {}".format(
                    MAX_UPGRADE_LEVEL, internal_level
                )
            )
        stored_levels.append(internal_level + 1)
    _write_text(path or UPGRADE_PATH, _format_list("gunLevel", stored_levels))


def read_upgrade_levels(path=None):
    """Read 1-based gunLevel values and return internal 0-based levels."""
    values = _parse_list(_read_text(path or UPGRADE_PATH), "gunLevel")
    upgrade_levels = []
    for value in values:
        stored_level = _parse_int(value, "gun level")
        if stored_level < 1 or stored_level > MAX_UPGRADE_LEVEL + 1:
            raise SaveDataError(
                "gunLevel must be between 1 and {}: {}".format(
                    MAX_UPGRADE_LEVEL + 1, stored_level
                )
            )
        upgrade_levels.append(stored_level - 1)
    return upgrade_levels


def write_coins(coins, path=None):
    """Write the coin amount to coins.txt."""
    amount = _parse_int(coins, "coins")
    if amount < 0:
        raise SaveDataError("coins must be non-negative: {}".format(amount))
    _write_text(path or COINS_PATH, "coins = {}".format(amount))


def read_coins(path=None):
    """Read the coin amount from coins.txt."""
    text = _read_text(path or COINS_PATH)
    match = re.fullmatch(r"\s*coins\s*=\s*(-?\d+)\s*", text)
    if match is None:
        raise SaveDataError("invalid coins format")
    amount = _parse_int(match.group(1), "coins")
    if amount < 0:
        raise SaveDataError("coins must be non-negative: {}".format(amount))
    return amount
