"""Delayed HP bar that lingers briefly behind damage taken."""

import math


HP_TRAIL_DELAY_SECONDS = 0.35
HP_TRAIL_FULL_DRAIN_SECONDS = 0.45


class HpTrail:
    """Track the slow-following HP value drawn behind the current HP bar."""

    def __init__(
        self,
        hp,
        max_hp,
        delay=HP_TRAIL_DELAY_SECONDS,
        full_drain_seconds=HP_TRAIL_FULL_DRAIN_SECONDS,
    ):
        if max_hp <= 0:
            raise ValueError("max_hp must be positive")
        if delay < 0:
            raise ValueError("delay must be non-negative")
        if full_drain_seconds <= 0:
            raise ValueError("full_drain_seconds must be positive")
        self.delay = float(delay)
        self.full_drain_seconds = float(full_drain_seconds)
        self.max_hp = float(max_hp)
        self.value = float(hp)
        self.target = float(hp)
        self._delay_remaining = 0.0

    @property
    def ratio(self):
        return min(max(self.value / self.max_hp, 0.0), 1.0)

    def reset(self, hp, max_hp=None):
        """Snap the trailing value to hp without any animation."""
        if max_hp is not None:
            if max_hp <= 0:
                raise ValueError("max_hp must be positive")
            self.max_hp = float(max_hp)
        self.value = float(hp)
        self.target = float(hp)
        self._delay_remaining = 0.0

    def update(self, hp, delta_time):
        """Advance the trailing bar towards the current hp value."""
        if not math.isfinite(delta_time) or delta_time < 0:
            raise ValueError("delta_time must be a finite non-negative number")
        hp = float(hp)
        if hp > self.target or hp >= self.value:
            self.reset(hp)
            return
        if hp < self.target:
            self.target = hp
            self._delay_remaining = max(0.0, self.delay - delta_time)
            return
        self.target = hp
        if self._delay_remaining > 0.0:
            self._delay_remaining = max(0.0, self._delay_remaining - delta_time)
            return
        drain_per_second = self.max_hp / self.full_drain_seconds
        self.value = max(hp, self.value - drain_per_second * delta_time)
