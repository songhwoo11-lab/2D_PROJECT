"""Shared weapon data and state used by every gun."""

from dataclasses import dataclass, replace
from enum import Enum
import math

from game_config import (
    AUTO_SHOT_HEAT_BASE,
    MACHINE_GUN_DAMAGE,
    MACHINE_GUN_FIRE_INTERVAL_SECONDS,
    MACHINE_GUN_MAGAZINE_SIZE,
    MACHINE_GUN_RELOAD_SECONDS,
    MACHINE_GUN_STARTING_AMMO,
    MACHINE_GUN_TEMPERATURE_LIMIT,
    AUTO_SHOT_HEAT_STEP,
    AUTO_STREAK_DECAY_SECONDS,
    COOLING_ACCELERATION_SCALE_SECONDS,
    FPS,
    COOLING_PER_SECOND_BLOCKED,
    COOLING_PER_SECOND_FIREABLE,
    COOLING_DAMAGE_PENALTY,
    COOLING_DAMAGE_PENALTY_DURATION,
    COOLING_TEMPERATURE_REDUCTION,
    MIN_TEMPERATURE,
    OVERHEAT_INITIAL_REDUCTION,
    OVERHEAT_REDUCTION_CURVE_EXPONENT,
    OVERHEAT_REDUCTION_HOLD_SECONDS,
    OVERHEAT_REDUCTION_RECOVERY_SECONDS,
    PISTOL_DAMAGE,
    PISTOL_FIRE_INTERVAL_SECONDS,
    PISTOL_MAGAZINE_SIZE,
    PISTOL_RELOAD_SECONDS,
    PISTOL_STARTING_AMMO,
    PISTOL_TEMPERATURE_LIMIT,
    RIFLE_DAMAGE,
    RIFLE_FIRE_INTERVAL_SECONDS,
    RIFLE_MAGAZINE_SIZE,
    RIFLE_RELOAD_SECONDS,
    RIFLE_STARTING_AMMO,
    RIFLE_TEMPERATURE_LIMIT,
    SINGLE_FIRE_INTERVAL_MULTIPLIER,
)


@dataclass(frozen=True)
class WeaponSpec:
    name: str
    damage: int
    fire_interval_seconds: float
    reload_seconds: float
    temperature_limit: float
    magazine_size: int
    starting_ammo: int


PISTOL = WeaponSpec(
    name="Pistol",
    damage=PISTOL_DAMAGE,
    fire_interval_seconds=PISTOL_FIRE_INTERVAL_SECONDS,
    reload_seconds=PISTOL_RELOAD_SECONDS,
    temperature_limit=PISTOL_TEMPERATURE_LIMIT,
    magazine_size=PISTOL_MAGAZINE_SIZE,
    starting_ammo=PISTOL_STARTING_AMMO,
)

RIFLE = WeaponSpec(
    name="Rifle",
    damage=RIFLE_DAMAGE,
    fire_interval_seconds=RIFLE_FIRE_INTERVAL_SECONDS,
    reload_seconds=RIFLE_RELOAD_SECONDS,
    temperature_limit=RIFLE_TEMPERATURE_LIMIT,
    magazine_size=RIFLE_MAGAZINE_SIZE,
    starting_ammo=RIFLE_STARTING_AMMO,
)

MACHINE_GUN = WeaponSpec(
    name="Machine Gun",
    damage=MACHINE_GUN_DAMAGE,
    fire_interval_seconds=MACHINE_GUN_FIRE_INTERVAL_SECONDS,
    reload_seconds=MACHINE_GUN_RELOAD_SECONDS,
    temperature_limit=MACHINE_GUN_TEMPERATURE_LIMIT,
    magazine_size=MACHINE_GUN_MAGAZINE_SIZE,
    starting_ammo=MACHINE_GUN_STARTING_AMMO,
)

DEFAULT_GUN_ID = "pistol"
RIFLE_GUN_ID = "rifle"
MACHINE_GUN_GUN_ID = "machine_gun"

WEAPON_SPECS = {
    DEFAULT_GUN_ID: PISTOL,
    RIFLE_GUN_ID: RIFLE,
    MACHINE_GUN_GUN_ID: MACHINE_GUN,
}


MAX_UPGRADE_LEVEL = 10


@dataclass(frozen=True)
class WeaponUpgradeEffects:
    damage: tuple
    magazine_size: tuple
    reload_seconds: tuple


UPGRADE_EFFECTS = {
    DEFAULT_GUN_ID: WeaponUpgradeEffects(
        damage=(5, 6, 6, 7, 7, 8, 8, 10, 10, 10, 10),
        magazine_size=(10, 10, 12, 12, 14, 14, 16, 16, 20, 20, 20),
        reload_seconds=(2.0, 2.0, 2.0, 2.0, 1.5, 1.5, 1.5, 1.5, 1.5, 1.0, 1.0),
    ),
    RIFLE_GUN_ID: WeaponUpgradeEffects(
        damage=(20, 25, 25, 30, 30, 35, 35, 40, 40, 40, 40),
        magazine_size=(30, 30, 35, 35, 40, 40, 45, 45, 50, 50, 50),
        reload_seconds=(3.0, 3.0, 3.0, 3.0, 2.2, 2.2, 2.2, 2.2, 2.2, 1.6, 1.6),
    ),
    MACHINE_GUN_GUN_ID: WeaponUpgradeEffects(
        damage=(12, 14, 14, 16, 16, 20, 20, 24, 24, 24, 24),
        magazine_size=(50, 50, 70, 70, 90, 90, 110, 110, 150, 150, 150),
        reload_seconds=(5.0, 5.0, 5.0, 5.0, 3.5, 3.5, 3.5, 3.5, 3.5, 2.0, 2.0),
    ),
}


def upgrade_effects(gun_id):
    if gun_id not in UPGRADE_EFFECTS:
        raise KeyError("unknown gun: {}".format(gun_id))
    return UPGRADE_EFFECTS[gun_id]


def weapon_stats_at_level(gun_id, level):
    if not isinstance(level, int) or not 0 <= level <= MAX_UPGRADE_LEVEL:
        raise ValueError("upgrade level must be between 0 and 10")
    spec = weapon_spec(gun_id)
    if level == 0:
        return spec
    effects = upgrade_effects(gun_id)
    return replace(
        spec,
        damage=effects.damage[level],
        magazine_size=effects.magazine_size[level],
        reload_seconds=effects.reload_seconds[level],
    )


def weapon_spec(gun_id):
    """Return the weapon data registered for the given gun id."""
    if gun_id not in WEAPON_SPECS:
        raise KeyError("unknown gun: {}".format(gun_id))
    return WEAPON_SPECS[gun_id]


def weapon_display_name(gun_id):
    """Return the name shown for the given gun id."""
    if gun_id in WEAPON_SPECS:
        return WEAPON_SPECS[gun_id].name.upper()
    return gun_id.upper()


def weapon_spec_or_default(gun_id):
    """Return the weapon data of the gun id, or the pistol when it is unknown."""
    return WEAPON_SPECS.get(gun_id, WEAPON_SPECS[DEFAULT_GUN_ID])


def gun_id_for_spec(spec):
    """Return the registered id of a weapon spec, or the default id."""
    for gun_id, registered in WEAPON_SPECS.items():
        if registered is spec:
            return gun_id
    return DEFAULT_GUN_ID


class FireMode(Enum):
    SINGLE = "single"
    AUTO = "auto"


class Gun:
    def __init__(self, spec=PISTOL, gun_id=None):
        if spec.magazine_size <= 0 or spec.starting_ammo < 0:
            raise ValueError("weapon ammunition values are invalid")
        self.spec = spec
        self._gun_id = gun_id
        self.infinite_ammo = False
        self.reset()

    @classmethod
    def from_gun_id(cls, gun_id, level=0):
        spec = weapon_stats_at_level(gun_id, level)
        return cls(spec, gun_id=gun_id)

    @property
    def gun_id(self):
        if self._gun_id is not None:
            return self._gun_id
        return gun_id_for_spec(self.spec)

    def reset(self):
        self.magazine_ammo = min(self.magazine_size, self.starting_ammo)
        self.reserve_ammo = self.starting_ammo - self.magazine_ammo
        self.cooldown_remaining = 0.0
        self.reload_remaining = 0.0
        self.fire_mode = FireMode.SINGLE
        self.infinite_ammo = False
        self.heat_enabled = True
        self.temperature = MIN_TEMPERATURE
        self.overheated = False
        self._idle_seconds = 0.0
        self._reset_auto_streak()
        self._damage_reduction_elapsed = None
        self._cooling_penalty_elapsed = None
        self._cooling_penalty_initial = 0.0

    @property
    def reloading(self):
        return self.reload_remaining > 0.0

    @property
    def temperature_limit(self):
        return self.spec.temperature_limit

    @property
    def fire_interval_seconds(self):
        return self.spec.fire_interval_seconds

    @property
    def fire_interval_frames(self):
        return self.spec.fire_interval_seconds * FPS

    @property
    def magazine_size(self):
        return self.spec.magazine_size

    @property
    def starting_ammo(self):
        return self.spec.starting_ammo

    @property
    def reload_seconds(self):
        return self.spec.reload_seconds

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
        total = 0.0
        elapsed = self._damage_reduction_elapsed
        if elapsed is not None:
            if elapsed < OVERHEAT_REDUCTION_HOLD_SECONDS:
                total += OVERHEAT_INITIAL_REDUCTION
            else:
                recovery_elapsed = elapsed - OVERHEAT_REDUCTION_HOLD_SECONDS
                if recovery_elapsed < OVERHEAT_REDUCTION_RECOVERY_SECONDS:
                    curve = (
                        math.exp(OVERHEAT_REDUCTION_CURVE_EXPONENT)
                        - math.exp(
                            OVERHEAT_REDUCTION_CURVE_EXPONENT
                            * recovery_elapsed
                            / OVERHEAT_REDUCTION_RECOVERY_SECONDS
                        )
                    ) / (math.exp(OVERHEAT_REDUCTION_CURVE_EXPONENT) - 1.0)
                    total += OVERHEAT_INITIAL_REDUCTION * curve
        # 냉각 아이템 패널티
        cooling_elapsed = self._cooling_penalty_elapsed
        if cooling_elapsed is not None:
            duration = COOLING_DAMAGE_PENALTY_DURATION
            if cooling_elapsed < duration:
                curve = (
                    math.exp(OVERHEAT_REDUCTION_CURVE_EXPONENT)
                    - math.exp(
                        OVERHEAT_REDUCTION_CURVE_EXPONENT
                        * cooling_elapsed
                        / duration
                    )
                ) / (math.exp(OVERHEAT_REDUCTION_CURVE_EXPONENT) - 1.0)
                total += self._cooling_penalty_initial * curve
            else:
                self._cooling_penalty_elapsed = None
        return min(1.0, total)

    @property
    def damage_reduction_remaining(self):
        remaining = 0.0
        elapsed = self._damage_reduction_elapsed
        if elapsed is not None:
            if elapsed < OVERHEAT_REDUCTION_HOLD_SECONDS:
                remaining = max(remaining, OVERHEAT_REDUCTION_HOLD_SECONDS - elapsed)
            else:
                recovery_elapsed = elapsed - OVERHEAT_REDUCTION_HOLD_SECONDS
                remaining = max(
                    remaining,
                    max(0.0, OVERHEAT_REDUCTION_RECOVERY_SECONDS - recovery_elapsed),
                )
        cooling_elapsed = self._cooling_penalty_elapsed
        if cooling_elapsed is not None:
            remaining = max(
                remaining,
                max(0.0, COOLING_DAMAGE_PENALTY_DURATION - cooling_elapsed),
            )
        return remaining

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
        self._idle_seconds += delta_time
        self._decay_auto_streak(delta_time)
        self._update_damage_reduction(delta_time)
        self._update_cooling_penalty(delta_time)
        self._cool(delta_time)

    @property
    def cooling_rate(self):
        """Temperature drop per second while the gun is not overheating.

        The rate grows quadratically the longer the gun stays idle.
        """
        ramp = self._idle_seconds / COOLING_ACCELERATION_SCALE_SECONDS
        return COOLING_PER_SECOND_FIREABLE * (1.0 + ramp * ramp)

    def _cool(self, delta_time):
        if self.overheated:
            self.temperature = max(
                MIN_TEMPERATURE,
                self.temperature - COOLING_PER_SECOND_BLOCKED * delta_time,
            )
            if self.temperature <= MIN_TEMPERATURE:
                self.temperature = MIN_TEMPERATURE
                self.overheated = False
                self._reset_auto_streak()
                self._damage_reduction_elapsed = 0.0
            return
        self.temperature = max(
            MIN_TEMPERATURE,
            self.temperature - self.cooling_rate * delta_time,
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

    def apply_cooling_item(self):
        """Apply the cooling pickup: reduce temperature and add a damage penalty."""
        if self.overheated:
            return False
        self.temperature = max(
            MIN_TEMPERATURE,
            self.temperature * (1.0 - COOLING_TEMPERATURE_REDUCTION),
        )
        self._reset_auto_streak()
        self._cooling_penalty_elapsed = 0.0
        self._cooling_penalty_initial = COOLING_DAMAGE_PENALTY
        return True

    def _update_cooling_penalty(self, delta_time):
        if self._cooling_penalty_elapsed is None:
            return
        self._cooling_penalty_elapsed += delta_time
        if self._cooling_penalty_elapsed >= COOLING_DAMAGE_PENALTY_DURATION:
            self._cooling_penalty_elapsed = None

    def _reset_auto_streak(self):
        self.auto_shot_streak = 0
        self._auto_idle_seconds = 0.0

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
        if self.magazine_ammo >= self.magazine_size or self.reserve_ammo <= 0:
            return False
        self.reload_remaining = self.reload_seconds
        if self.reload_remaining <= 0:
            self._finish_reload()
        return True

    def _finish_reload(self):
        needed = self.magazine_size - self.magazine_ammo
        loaded = min(needed, self.reserve_ammo)
        self.magazine_ammo += loaded
        self.reserve_ammo -= loaded
        self.reload_remaining = 0.0

    def add_reserve_ammo(self, amount):
        if amount < 0:
            raise ValueError("reserve amount must be non-negative")
        added = int(amount)
        self.reserve_ammo += added
        return added

    def try_fire(self):
        if not self.can_fire:
            return False
        if not self.infinite_ammo:
            self.magazine_ammo -= 1
        fire_interval = self.fire_interval_seconds
        if self.fire_mode is FireMode.SINGLE:
            fire_interval *= SINGLE_FIRE_INTERVAL_MULTIPLIER
        if self.heat_enabled:
            self.auto_shot_streak += 1
            self._auto_idle_seconds = 0.0
        self._add_heat(
            AUTO_SHOT_HEAT_BASE
            + AUTO_SHOT_HEAT_STEP * (self.auto_shot_streak - 1)
        )
        self._idle_seconds = 0.0
        self.cooldown_remaining = fire_interval
        return True

    def _add_heat(self, amount):
        if not self.heat_enabled:
            return
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


class WeaponStates:
    def __init__(self, gun_ids=None, initial_gun_id=DEFAULT_GUN_ID):
        ids = tuple(gun_ids) if gun_ids is not None else tuple(WEAPON_SPECS)
        if not ids:
            raise ValueError("at least one gun is required")
        for gun_id in ids:
            weapon_spec(gun_id)
        if initial_gun_id not in ids:
            raise ValueError("initial gun is not managed: {}".format(initial_gun_id))
        self.gun_ids = ids
        self.current_id = initial_gun_id
        self._states = {
            gun_id: self._capture(Gun.from_gun_id(gun_id)) for gun_id in self.gun_ids
        }
        self.gun = Gun.from_gun_id(self.current_id)
        self._restore(self.current_id)

    @staticmethod
    def _capture(gun):
        return {
            "magazine_ammo": gun.magazine_ammo,
            "reserve_ammo": gun.reserve_ammo,
            "cooldown_remaining": gun.cooldown_remaining,
            "reload_remaining": gun.reload_remaining,
            "fire_mode": gun.fire_mode,
            "infinite_ammo": gun.infinite_ammo,
            "heat_enabled": gun.heat_enabled,
            "temperature": gun.temperature,
            "overheated": gun.overheated,
            "auto_shot_streak": gun.auto_shot_streak,
            "auto_idle_seconds": gun._auto_idle_seconds,
            "idle_seconds": gun._idle_seconds,
            "damage_reduction_elapsed": gun._damage_reduction_elapsed,
            "cooling_penalty_elapsed": gun._cooling_penalty_elapsed,
            "cooling_penalty_initial": gun._cooling_penalty_initial,
        }

    def _save_current(self):
        self._states[self.current_id] = self._capture(self.gun)

    def _restore(self, gun_id):
        state = self._states[gun_id]
        self.gun.magazine_ammo = state["magazine_ammo"]
        self.gun.reserve_ammo = state["reserve_ammo"]
        self.gun.cooldown_remaining = state["cooldown_remaining"]
        self.gun.reload_remaining = state["reload_remaining"]
        self.gun.fire_mode = state["fire_mode"]
        self.gun.infinite_ammo = state["infinite_ammo"]
        self.gun.heat_enabled = state["heat_enabled"]
        self.gun.temperature = state["temperature"]
        self.gun.overheated = state["overheated"]
        self.gun.auto_shot_streak = state["auto_shot_streak"]
        self.gun._auto_idle_seconds = state["auto_idle_seconds"]
        self.gun._idle_seconds = state["idle_seconds"]
        self.gun._damage_reduction_elapsed = state["damage_reduction_elapsed"]
        self.gun._cooling_penalty_elapsed = state["cooling_penalty_elapsed"]
        self.gun._cooling_penalty_initial = state["cooling_penalty_initial"]

    @property
    def ammo_snapshot(self):
        self._save_current()
        return {
            gun_id: (
                state["magazine_ammo"],
                state["reserve_ammo"],
            )
            for gun_id, state in self._states.items()
        }

    @property
    def state_snapshot(self):
        self._save_current()
        return {gun_id: dict(state) for gun_id, state in self._states.items()}

    def select(self, gun_id):
        if gun_id not in self._states:
            raise ValueError("gun is not managed: {}".format(gun_id))
        if gun_id == self.current_id:
            return self.gun
        self._save_current()
        self.current_id = gun_id
        self.gun.spec = weapon_spec(gun_id)
        self._restore(gun_id)
        return self.gun
