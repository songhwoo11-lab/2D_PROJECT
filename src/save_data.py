"""Save data model and defaults for the game file storage."""

from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from shop import GUN_SHOP_ORDER


RECENT_LOG_LIMIT = 10


@dataclass(frozen=True)
class BestLog:
    """Best reached wave and the time taken to reach it."""

    reached_wave: int
    elapsed_time: float


@dataclass
class SaveData:
    """All values that are written to the game files."""

    acquired_guns: List[bool] = field(default_factory=list)
    upgrade_levels: List[int] = field(default_factory=list)
    coins: int = 0
    best_log: Optional[BestLog] = None
    recent_logs: List[Tuple[int, float]] = field(default_factory=list)
    training_records: List[int] = field(default_factory=list)


def _as_log_pair(entry):
    """Accept either a BestLog or a plain wave/time pair."""
    if isinstance(entry, BestLog):
        return entry.reached_wave, entry.elapsed_time
    wave, elapsed_time = entry
    return wave, elapsed_time


def select_best_log(logs):
    """Choose the highest wave; break ties with the shortest play time."""
    candidates = [_as_log_pair(entry) for entry in logs]
    if not candidates:
        return None
    wave, elapsed_time = max(
        candidates, key=lambda entry: (entry[0], -float(entry[1]))
    )
    return BestLog(reached_wave=wave, elapsed_time=elapsed_time)


def limit_recent_logs(logs, limit=RECENT_LOG_LIMIT):
    """Keep only the newest recent records in their existing order."""
    if limit < 1:
        raise ValueError("recent log limit must be positive")
    return [tuple(entry) for entry in list(logs)[:limit]]


@dataclass
class SaveLoadResult:
    """Loaded data together with guidance about missing or damaged files."""

    data: SaveData
    messages: List[str] = field(default_factory=list)
    recovered: bool = False

    def guidance_text(self):
        """Return the messages joined for display to the player."""
        return " ".join(self.messages)


def default_save_data():
    """Build the state used on a first run of the game."""
    return SaveData(
        acquired_guns=[index == 0 for index in range(len(GUN_SHOP_ORDER))],
        upgrade_levels=[0 for _ in GUN_SHOP_ORDER],
        coins=0,
        best_log=None,
        recent_logs=[],
        training_records=[],
    )
