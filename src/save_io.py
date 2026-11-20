"""Read and write the individual game files in the PRD text formats."""

import re

from save_paths import GUNS_PATH


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
