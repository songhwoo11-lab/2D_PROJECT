"""Battle result record helpers shared by the battle scene and lobby."""

from dataclasses import dataclass

VICTORY = "victory"


@dataclass(frozen=True)
class BattleRecord:
    """One finished battle and the result it produced."""

    result: str
    reached_wave: int
    elapsed_time: float
    clear_time: float = None


def format_elapsed_time(seconds):
    if seconds < 0:
        raise ValueError("elapsed time must be non-negative")
    minutes = int(seconds // 60)
    remaining = seconds - minutes * 60
    return "{}:{:04.1f}".format(minutes, remaining)


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
