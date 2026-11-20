"""Read and write the individual game files in the PRD text formats."""

import math
import re

from game_config import TOTAL_WAVES
from save_data import BestLog, SaveData, SaveLoadResult, default_save_data
from save_paths import (
    BEST_LOG_PATH,
    COINS_PATH,
    GUNS_PATH,
    RECENT_LOG_PATH,
    TRAINING_LOG_PATH,
    UPGRADE_PATH,
    ensure_gamefile_directories,
    gamefile_paths,
)
from shop import GUN_SHOP_ORDER, MAX_UPGRADE_LEVEL


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


def _parse_float(value, label):
    try:
        number = float(value)
    except (TypeError, ValueError) as error:
        raise SaveDataError("invalid {} value: {}".format(label, value)) from error
    if not math.isfinite(number):
        raise SaveDataError("{} must be finite: {}".format(label, value))
    return number


def _format_number(value):
    number = _parse_float(value, "number")
    return str(int(number)) if number.is_integer() else str(number)


def _parse_number_pair(text, key):
    values = _parse_list(text, key)
    if len(values) != 2:
        raise SaveDataError("{} must contain two values".format(key))
    return values


def write_best_log(best_log, path=None):
    """Write the best wave and time, using [0, 0] when there is no record."""
    if best_log is None:
        values = [0, 0]
    else:
        wave = _parse_int(best_log.reached_wave, "reached wave")
        elapsed_time = _parse_float(best_log.elapsed_time, "play time")
        if wave < 1 or wave > TOTAL_WAVES:
            raise SaveDataError(
                "reached wave must be between 1 and {}: {}".format(
                    TOTAL_WAVES, wave
                )
            )
        if elapsed_time < 0:
            raise SaveDataError("play time must be non-negative")
        values = [wave, _format_number(elapsed_time)]
    _write_text(
        path or BEST_LOG_PATH,
        "BestLog = [{}]".format(", ".join(str(value) for value in values)),
    )


def read_best_log(path=None):
    """Read the best record; the [0, 0] sentinel means no record yet."""
    values = _parse_number_pair(_read_text(path or BEST_LOG_PATH), "BestLog")
    wave = _parse_int(values[0], "reached wave")
    elapsed_time = _parse_float(values[1], "play time")
    if elapsed_time < 0:
        raise SaveDataError("play time must be non-negative")
    if wave == 0:
        if elapsed_time != 0:
            raise SaveDataError("empty best log must use [0, 0]")
        return None
    if wave < 1 or wave > TOTAL_WAVES:
        raise SaveDataError(
            "reached wave must be between 1 and {}: {}".format(TOTAL_WAVES, wave)
        )
    return BestLog(reached_wave=wave, elapsed_time=elapsed_time)


def _validate_recent_entry(wave, elapsed_time):
    if wave < 1 or wave > TOTAL_WAVES:
        raise SaveDataError(
            "reached wave must be between 1 and {}: {}".format(TOTAL_WAVES, wave)
        )
    if elapsed_time < 0:
        raise SaveDataError("play time must be non-negative")


def _as_pair(entry, label):
    try:
        first, second = entry
    except (TypeError, ValueError) as error:
        raise SaveDataError("{} must contain two values".format(label)) from error
    return first, second


def write_recent_logs(recent_logs, path=None):
    """Write the recent wave/time pairs to latelyLog.txt."""
    entries = []
    for index, entry in enumerate(recent_logs):
        raw_wave, raw_time = _as_pair(entry, "recent log")
        wave = _parse_int(raw_wave, "reached wave")
        elapsed_time = _parse_float(raw_time, "play time")
        _validate_recent_entry(wave, elapsed_time)
        entries.append("[{}, {}]".format(wave, _format_number(elapsed_time)))
    _write_text(
        path or RECENT_LOG_PATH,
        "log = [{}]".format(", ".join(entries)),
    )


def read_recent_logs(path=None):
    """Read the recent wave/time pairs from latelyLog.txt."""
    text = _read_text(path or RECENT_LOG_PATH)
    match = re.fullmatch(r"\s*log\s*=\s*\[(.*)\]\s*", text, flags=re.DOTALL)
    if match is None:
        raise SaveDataError("invalid log format")
    inner = match.group(1).strip()
    if not inner:
        return []
    entries = re.findall(
        r"\[\s*([^,\[\]]+?)\s*,\s*([^,\[\]]+?)\s*\]", inner
    )
    rebuilt = ", ".join(
        "[{}, {}]".format(raw_wave.strip(), raw_time.strip())
        for raw_wave, raw_time in entries
    )
    if re.sub(r"\s+", "", rebuilt) != re.sub(r"\s+", "", inner):
        raise SaveDataError("invalid log entry format")
    recent_logs = []
    for raw_wave, raw_time in entries:
        wave = _parse_int(raw_wave, "reached wave")
        elapsed_time = _parse_float(raw_time, "play time")
        _validate_recent_entry(wave, elapsed_time)
        recent_logs.append((wave, elapsed_time))
    return recent_logs


def write_training_records(training_records, path=None):
    """Write destroyed-target counts to trainingLog.txt."""
    values = []
    for value in training_records:
        count = _parse_int(value, "destroyed targets")
        if count < 0:
            raise SaveDataError("destroyed targets must be non-negative")
        values.append(count)
    _write_text(
        path or TRAINING_LOG_PATH,
        "trainingLog = [{}]".format(", ".join(str(value) for value in values)),
    )


def read_training_records(path=None):
    """Read destroyed-target counts from trainingLog.txt."""
    values = _parse_list(
        _read_text(path or TRAINING_LOG_PATH), "trainingLog"
    )
    records = []
    for value in values:
        count = _parse_int(value, "destroyed targets")
        if count < 0:
            raise SaveDataError("destroyed targets must be non-negative")
        records.append(count)
    return records


def _require_fields(data, field_names):
    values = getattr(data, "__dict__", None)
    for name in field_names:
        if values is None:
            if not hasattr(data, name):
                raise SaveDataError("missing save field: {}".format(name))
        elif name not in values:
            raise SaveDataError("missing save field: {}".format(name))


def _require_list(value, label, length=None):
    if not isinstance(value, (list, tuple)):
        raise SaveDataError("{} must be a list".format(label))
    if length is not None and len(value) != length:
        raise SaveDataError(
            "{} must contain {} entries: got {}".format(label, length, len(value))
        )


def _require_int(value, label, minimum=None, maximum=None):
    if isinstance(value, bool) or not isinstance(value, int):
        raise SaveDataError("{} must be an integer: {!r}".format(label, value))
    if minimum is not None and value < minimum:
        raise SaveDataError("{} must be at least {}".format(label, minimum))
    if maximum is not None and value > maximum:
        raise SaveDataError("{} must be at most {}".format(label, maximum))
    return value


def _require_time(value, label):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise SaveDataError("{} must be a number: {!r}".format(label, value))
    number = float(value)
    if not math.isfinite(number) or number < 0:
        raise SaveDataError("{} must be a finite non-negative number".format(label))
    return number


def validate_save_data(data):
    """Check every save field for missing values, wrong types, and bad ranges."""
    field_names = (
        "acquired_guns",
        "upgrade_levels",
        "coins",
        "best_log",
        "recent_logs",
        "training_records",
    )
    _require_fields(data, field_names)
    expected_count = len(GUN_SHOP_ORDER)

    _require_list(data.acquired_guns, "acquired_guns", expected_count)
    for owned in data.acquired_guns:
        if not isinstance(owned, bool):
            raise SaveDataError("gun ownership must be a boolean: {!r}".format(owned))

    _require_list(data.upgrade_levels, "upgrade_levels", expected_count)
    for level in data.upgrade_levels:
        _require_int(level, "upgrade level", 0, MAX_UPGRADE_LEVEL)

    _require_int(data.coins, "coins", 0)

    if data.best_log is not None:
        _require_fields(data.best_log, ("reached_wave", "elapsed_time"))
        wave = _require_int(
            data.best_log.reached_wave, "best reached wave", 0, TOTAL_WAVES
        )
        elapsed_time = _require_time(data.best_log.elapsed_time, "best play time")
        if wave == 0 and elapsed_time != 0:
            raise SaveDataError("empty best log must use wave and time zero")

    _require_list(data.recent_logs, "recent_logs")
    for index, entry in enumerate(data.recent_logs):
        raw_wave, raw_time = _as_pair(entry, "recent log")
        _require_int(raw_wave, "recent log reached wave", 1, TOTAL_WAVES)
        _require_time(raw_time, "recent log play time")

    _require_list(data.training_records, "training_records")
    for count in data.training_records:
        _require_int(count, "destroyed targets", 0)
    return True


_SAVE_FIELDS = (
    ("guns", "acquired_guns", read_guns),
    ("upgrades", "upgrade_levels", read_upgrade_levels),
    ("coins", "coins", read_coins),
    ("best_log", "best_log", read_best_log),
    ("recent_logs", "recent_logs", read_recent_logs),
    ("training_records", "training_records", read_training_records),
)


def write_save_data(data, root=None):
    """Write every game file from a SaveData object."""
    validate_save_data(data)
    paths = gamefile_paths(root)
    ensure_gamefile_directories(root)
    write_guns(data.acquired_guns, paths["guns"])
    write_upgrade_levels(data.upgrade_levels, paths["upgrades"])
    write_coins(data.coins, paths["coins"])
    write_best_log(data.best_log, paths["best_log"])
    write_recent_logs(data.recent_logs, paths["recent_logs"])
    write_training_records(data.training_records, paths["training_records"])


def _new_default_data():
    """Return an independent copy of the first-run save state."""
    defaults = default_save_data()
    return SaveData(
        acquired_guns=list(defaults.acquired_guns),
        upgrade_levels=list(defaults.upgrade_levels),
        coins=defaults.coins,
        best_log=defaults.best_log,
        recent_logs=list(defaults.recent_logs),
        training_records=list(defaults.training_records),
    )


def _write_missing_files(data, paths, missing_paths):
    """Create only the files that were absent before loading."""
    writers = {
        "guns": lambda path: write_guns(data.acquired_guns, path),
        "upgrades": lambda path: write_upgrade_levels(data.upgrade_levels, path),
        "coins": lambda path: write_coins(data.coins, path),
        "best_log": lambda path: write_best_log(data.best_log, path),
        "recent_logs": lambda path: write_recent_logs(data.recent_logs, path),
        "training_records": lambda path: write_training_records(
            data.training_records, path
        ),
    }
    for key in paths:
        if paths[key] in missing_paths:
            writers[key](paths[key])


def load_save_data_with_report(root=None):
    """Load save data and report missing files, damage, and recovery."""
    paths = gamefile_paths(root)
    ensure_gamefile_directories(root)
    data = _new_default_data()
    messages = []
    recovered = False
    missing = []
    for key, field_name, reader in _SAVE_FIELDS:
        path = paths[key]
        if not path.exists():
            missing.append(path)
            continue
        try:
            setattr(data, field_name, reader(path))
        except (SaveDataError, OSError, ValueError) as error:
            messages.append(
                "저장 파일을 읽을 수 없어 기본값으로 복구했습니다: {} ({})".format(
                    path.name, error
                )
            )
            recovered = True
    if missing:
        _write_missing_files(data, paths, missing)
        messages.append(
            "저장 파일이 없어 기본값을 생성했습니다: {}".format(
                ", ".join(path.name for path in missing)
            )
        )
    try:
        validate_save_data(data)
    except SaveDataError as error:
        messages.append(
            "저장 데이터가 유효하지 않아 전체 기본값으로 복구했습니다: {}".format(
                error
            )
        )
        data = _new_default_data()
        recovered = True
    return SaveLoadResult(data=data, messages=messages, recovered=recovered)


def load_save_data(root=None):
    """Load all game files, creating PRD defaults for any missing file."""
    return load_save_data_with_report(root).data
