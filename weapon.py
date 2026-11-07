"""Weapon data and state used by the first-stage pistol."""

from dataclasses import dataclass
from enum import Enum
import math

from game_config import (
    FPS,
    PISTOL_DAMAGE,
    PISTOL_FIRE_INTERVAL_FRAMES,
    PISTOL_MAGAZINE_SIZE,
    PISTOL_RELOAD_SECONDS,
    PISTOL_STARTING_AMMO,
    PISTOL_TEMPERATURE_LIMIT,
)


@dataclass(frozen=True)
class WeaponSpec:
    name: str
    damage: int
    fire_interval_frames: int
    reload_seconds: float
    temperature_limit: float
    magazine_size: int
    starting_ammo: int

    @property
    def fire_interval_seconds(self):
        return self.fire_interval_frames / FPS


PISTOL = WeaponSpec(
    name="Pistol",
    damage=PISTOL_DAMAGE,
    fire_interval_frames=PISTOL_FIRE_INTERVAL_FRAMES,
    reload_seconds=PISTOL_RELOAD_SECONDS,
    temperature_limit=PISTOL_TEMPERATURE_LIMIT,
    magazine_size=PISTOL_MAGAZINE_SIZE,
    starting_ammo=PISTOL_STARTING_AMMO,
)


class FireMode(Enum):
    SINGLE = "single"
    AUTO = "auto"


class Gun:
    def __init__(self, spec=PISTOL):
        if spec.magazine_size <= 0 or spec.starting_ammo < 0:
            raise ValueError("weapon ammunition values are invalid")
        self.spec = spec
        self.magazine_ammo = min(spec.magazine_size, spec.starting_ammo)
        self.reserve_ammo = spec.starting_ammo - self.magazine_ammo
        self.cooldown_remaining = 0.0
        self.reloading = False
        self.fire_mode = FireMode.SINGLE

    @property
    def total_ammo(self):
        return self.magazine_ammo + self.reserve_ammo

    @property
    def can_fire(self):
        return (
            not self.reloading
            and self.magazine_ammo > 0
            and self.cooldown_remaining <= 1e-9
        )

    def update(self, delta_time):
        if not math.isfinite(delta_time) or delta_time < 0:
            raise ValueError("delta_time must be a finite non-negative number")
        self.cooldown_remaining = max(0.0, self.cooldown_remaining - delta_time)

    def try_fire(self):
        if not self.can_fire:
            return False
        self.magazine_ammo -= 1
        self.cooldown_remaining = self.spec.fire_interval_seconds
        return True

    def toggle_mode(self):
        self.fire_mode = (
            FireMode.AUTO
            if self.fire_mode is FireMode.SINGLE
            else FireMode.SINGLE
        )
        return self.fire_mode

    def handle_fire_input(self, mouse_held, mouse_pressed=False):
        if self.fire_mode is FireMode.SINGLE:
            return self.try_fire() if mouse_pressed else False
        return self.try_fire() if mouse_held else False
