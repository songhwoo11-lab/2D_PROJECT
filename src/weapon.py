"""Weapon data and state used by the first-stage pistol."""

from dataclasses import dataclass
from enum import Enum
import math

from game_config import (
    AUTO_SHOT_HEAT_BASE,
    AUTO_SHOT_HEAT_STEP,
    AUTO_STREAK_DECAY_SECONDS,
    COOLING_PER_FRAME_BLOCKED,
    COOLING_PER_FRAME_FIREABLE,
    FPS,
    MIN_TEMPERATURE,
    OVERHEAT_INITIAL_REDUCTION,
    OVERHEAT_REDUCTION_HOLD_SECONDS,
    OVERHEAT_REDUCTION_RECOVERY_SECONDS,
    PISTOL_DAMAGE,
    PISTOL_FIRE_INTERVAL_FRAMES,
    PISTOL_MAGAZINE_SIZE,
    PISTOL_RELOAD_SECONDS,
    PISTOL_STARTING_AMMO,
    PISTOL_TEMPERATURE_LIMIT,
    SINGLE_SHOT_HEAT,
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
        self.infinite_ammo = False
        self.reset()

    def reset(self):
        self.magazine_ammo = min(self.spec.magazine_size, self.spec.starting_ammo)
        self.reserve_ammo = self.spec.starting_ammo - self.magazine_ammo
        self.cooldown_remaining = 0.0
        self.reload_remaining = 0.0
        self.fire_mode = FireMode.SINGLE
        self.infinite_ammo = False
        self.temperature = MIN_TEMPERATURE
        self.overheated = False
        self.auto_shot_streak = 0
        self._auto_idle_seconds = 0.0
        self._damage_reduction_elapsed = None

    @property
    def reloading(self):
        return self.reload_remaining > 0.0

    @property
    def temperature_limit(self):
        return self.spec.temperature_limit

    @property
    def fire_blocked(self):
        return self.overheated

    @property
    def total_ammo(self):
        return self.magazine_ammo + self.reserve_ammo

    @property
    def can_fire(self):
        return (
            not self.overheated
            and not self.reloading
            and (self.infinite_ammo or self.magazine_ammo > 0)
            and self.cooldown_remaining <= 1e-9
        )

    @property
    def damage_reduction(self):
        elapsed = self._damage_reduction_elapsed
        if elapsed is None:
            return 0.0
        if elapsed < OVERHEAT_REDUCTION_HOLD_SECONDS:
            return OVERHEAT_INITIAL_REDUCTION
        recovery_elapsed = elapsed - OVERHEAT_REDUCTION_HOLD_SECONDS
        if recovery_elapsed >= OVERHEAT_REDUCTION_RECOVERY_SECONDS:
            return 0.0
        return (
            40.0
            * math.cos(
                math.pi
                * recovery_elapsed
                / OVERHEAT_REDUCTION_RECOVERY_SECONDS
            )
            + 40.0
        ) / 100.0

    @property
    def damage_multiplier(self):
        return 1.0 - self.damage_reduction

    @property
    def effective_damage(self):
        return self.spec.damage * self.damage_multiplier

    def update(self, delta_time):
        if not math.isfinite(delta_time) or delta_time < 0:
            raise ValueError("delta_time must be a finite non-negative number")
        self.cooldown_remaining = max(0.0, self.cooldown_remaining - delta_time)
        if self.reloading:
            self.reload_remaining = max(0.0, self.reload_remaining - delta_time)
            if self.reload_remaining <= 1e-9:
                self._finish_reload()
        self._decay_auto_streak(delta_time)
        self._cool(delta_time)
        self._update_damage_reduction(delta_time)

    def _cool(self, delta_time):
        if self.overheated:
            self.temperature = max(
                MIN_TEMPERATURE,
                self.temperature - COOLING_PER_FRAME_BLOCKED,
            )
            if self.temperature <= MIN_TEMPERATURE:
                self.temperature = MIN_TEMPERATURE
                self.overheated = False
                self._damage_reduction_elapsed = 0.0
            return
        self.temperature = max(
            MIN_TEMPERATURE,
            self.temperature - COOLING_PER_FRAME_FIREABLE,
        )

    def _update_damage_reduction(self, delta_time):
        if self._damage_reduction_elapsed is None:
            return
        self._damage_reduction_elapsed += delta_time
        if (
            self._damage_reduction_elapsed
            >= OVERHEAT_REDUCTION_HOLD_SECONDS
            + OVERHEAT_REDUCTION_RECOVERY_SECONDS
        ):
            self._damage_reduction_elapsed = None

    def _decay_auto_streak(self, delta_time):
        if self.auto_shot_streak <= 0:
            self._auto_idle_seconds = 0.0
            return
        self._auto_idle_seconds += delta_time
        while (
            self._auto_idle_seconds >= AUTO_STREAK_DECAY_SECONDS
            and self.auto_shot_streak > 0
        ):
            self._auto_idle_seconds -= AUTO_STREAK_DECAY_SECONDS
            self.auto_shot_streak -= 1

    def start_reload(self):
        if self.infinite_ammo or self.reloading:
            return False
        if self.magazine_ammo >= self.spec.magazine_size or self.reserve_ammo <= 0:
            return False
        self.reload_remaining = self.spec.reload_seconds
        if self.reload_remaining <= 0:
            self._finish_reload()
        return True

    def _finish_reload(self):
        needed = self.spec.magazine_size - self.magazine_ammo
        loaded = min(needed, self.reserve_ammo)
        self.magazine_ammo += loaded
        self.reserve_ammo -= loaded
        self.reload_remaining = 0.0

    def try_fire(self):
        if not self.can_fire:
            return False
        if not self.infinite_ammo:
            self.magazine_ammo -= 1
        fire_interval_frames = self.spec.fire_interval_frames
        if self.fire_mode is FireMode.SINGLE:
            fire_interval_frames *= 2
            self._add_heat(SINGLE_SHOT_HEAT)
        else:
            self.auto_shot_streak += 1
            self._auto_idle_seconds = 0.0
            self._add_heat(
                AUTO_SHOT_HEAT_BASE
                + AUTO_SHOT_HEAT_STEP * (self.auto_shot_streak - 1)
            )
        self.cooldown_remaining = fire_interval_frames / FPS
        return True

    def _add_heat(self, amount):
        self.temperature = min(
            self.temperature_limit,
            self.temperature + max(0.0, amount),
        )
        if self.temperature >= self.temperature_limit:
            self.temperature = self.temperature_limit
            self.overheated = True

    def toggle_mode(self):
        self.fire_mode = (
            FireMode.AUTO
            if self.fire_mode is FireMode.SINGLE
            else FireMode.SINGLE
        )
        return self.fire_mode

    def handle_fire_input(self, mouse_held, mouse_pressed=False):
        should_reload = (
            mouse_pressed
            if self.fire_mode is FireMode.SINGLE
            else mouse_held
        )
        if should_reload and not self.infinite_ammo and self.magazine_ammo <= 0:
            self.start_reload()
            return False
        if self.fire_mode is FireMode.SINGLE:
            return self.try_fire() if mouse_pressed else False
        return self.try_fire() if mouse_held else False
