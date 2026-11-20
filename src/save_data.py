"""Save data model and defaults for the game file storage."""

from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from shop import GUN_SHOP_ORDER


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
