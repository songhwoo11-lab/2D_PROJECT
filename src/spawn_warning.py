"""Short-lived marker that warns where an enemy is about to spawn."""

from game_config import SPAWN_WARNING_SECONDS


class SpawnWarning:
    def __init__(self, x, y, radius, duration=SPAWN_WARNING_SECONDS):
        if radius < 0:
            raise ValueError("warning radius must be non-negative")
        if duration < 0:
            raise ValueError("warning duration must be non-negative")
        self.x = float(x)
        self.y = float(y)
        self.radius = float(radius)
        self.duration = float(duration)
        self.remaining = float(duration)

    @property
    def is_expired(self):
        return self.remaining <= 0.0

    @property
    def progress(self):
        if self.duration <= 0:
            return 1.0
        return 1.0 - self.remaining / self.duration

    def update(self, delta_time):
        if delta_time < 0:
            raise ValueError("delta_time must be non-negative")
        self.remaining = max(0.0, self.remaining - delta_time)
