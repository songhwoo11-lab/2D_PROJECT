"""Weapon data and state used by the first-stage pistol."""

from dataclasses import dataclass

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


class Gun:
    def __init__(self, spec=PISTOL):
        if spec.magazine_size <= 0 or spec.starting_ammo < 0:
            raise ValueError("weapon ammunition values are invalid")
        self.spec = spec
        self.magazine_ammo = min(spec.magazine_size, spec.starting_ammo)
        self.reserve_ammo = spec.starting_ammo - self.magazine_ammo

    @property
    def total_ammo(self):
        return self.magazine_ammo + self.reserve_ammo
