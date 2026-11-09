"""Target-filtered explosion damage shared by explosive enemy behaviors."""

from enum import Enum
import math

from enemy import Enemy


class ExplosionTarget(Enum):
    PLAYER_ONLY = "player"
    ENEMIES_ONLY = "enemies"


class Explosion:
    def __init__(
        self,
        x,
        y,
        radius,
        damage,
        target,
        owner=None,
    ):
        if radius < 0:
            raise ValueError("explosion radius must be non-negative")
        if damage < 0:
            raise ValueError("explosion damage must be non-negative")
        self.x = float(x)
        self.y = float(y)
        self.radius = float(radius)
        self.damage = float(damage)
        self.target = target
        self.owner = owner
        self._applied = False

    def apply(self, player=None, enemies=()):
        if self._applied:
            return ()
        self._applied = True
        if self.target is ExplosionTarget.PLAYER_ONLY:
            candidates = (player,) if player is not None else ()
        elif self.target is ExplosionTarget.ENEMIES_ONLY:
            candidates = enemies
        else:
            raise ValueError("unsupported explosion target: {!r}".format(self.target))

        affected = []
        for candidate in candidates:
            if candidate is None or candidate is self.owner:
                continue
            if isinstance(candidate, Enemy) and not candidate.is_alive:
                continue
            distance = math.hypot(candidate.x - self.x, candidate.y - self.y)
            if distance <= self.radius:
                candidate.take_damage(self.damage)
                affected.append(candidate)
        return tuple(affected)
