"""Battle result record helpers shared by the battle scene and lobby."""

from dataclasses import dataclass

from game_config import DEFAULT_DIFFICULTY, TOTAL_WAVES, normalize_difficulty
from weapon import DEFAULT_GUN_ID, weapon_display_name

VICTORY = "victory"


@dataclass(frozen=True)
class BattleRecord:
    """One finished battle and the wave the player actually cleared."""

    result: str
    reached_wave: int
    elapsed_time: float
    clear_time: float = None
    gun_id: str = DEFAULT_GUN_ID
    cleared_wave: int = None
    difficulty: str = DEFAULT_DIFFICULTY


def cleared_wave_of(record):
    """Return the last fully cleared wave for a record."""
    if record.cleared_wave is not None:
        return record.cleared_wave
    if record.result == VICTORY:
        return TOTAL_WAVES
    return max(0, record.reached_wave - 1)


def cleared_time_of(record):
    """Return the time when the cleared wave was completed."""
    if record.clear_time is not None:
        return record.clear_time
    return record.elapsed_time


def complete_battle_record(record, difficulty=None):
    """Fill in derived fields on a record and drop runs that cleared no wave."""
    if not isinstance(record, BattleRecord):
        return None
    cleared_wave = cleared_wave_of(record)
    if cleared_wave < 1:
        return None
    record_difficulty = normalize_difficulty(
        difficulty
        if difficulty is not None
        else getattr(record, "difficulty", DEFAULT_DIFFICULTY)
    )
    return BattleRecord(
        result=record.result,
        reached_wave=max(record.reached_wave, cleared_wave),
        elapsed_time=record.elapsed_time,
        clear_time=cleared_time_of(record),
        gun_id=record.gun_id or DEFAULT_GUN_ID,
        cleared_wave=cleared_wave,
        difficulty=record_difficulty,
    )


@dataclass(frozen=True)
class TrainingRecord:
    """One finished training run and the targets destroyed in the time limit."""

    targets_destroyed: int


def training_record_text(targets_destroyed):
    return "TARGETS {}".format(targets_destroyed)


def format_elapsed_time(seconds):
    if seconds < 0:
        raise ValueError("elapsed time must be non-negative")
    minutes = int(seconds // 60)
    remaining = seconds - minutes * 60
    return "{}:{:04.1f}".format(minutes, remaining)


def battle_record_text(record):
    """Format a record as used by the difficulty-filtered records book."""
    return "{} WAVE {} TIME {}".format(
        weapon_display_name(record.gun_id),
        cleared_wave_of(record),
        format_elapsed_time(cleared_time_of(record)),
    )


def result_record_text(
    result_value,
    reached_wave,
    total_waves,
    elapsed_time,
    clear_time=None,
):
    if result_value == VICTORY:
        return "CLEAR TIME {}".format(
            format_elapsed_time(
                elapsed_time if clear_time is None else clear_time
            )
        )
    return "REACHED WAVE {}/{}".format(reached_wave, total_waves)
