"""Wave composition data for the 30-wave survival mode."""

from collections import OrderedDict, deque
import math
import random

from enemy import EnemyType
from game_config import (
    TOTAL_WAVES,
    WAVE_ENEMIES_PER_WAVE,
    WAVE_SPAWN_RATE_PER_SECOND,
    WAVE_STAT_MULTIPLIER_EVERY,
    WAVE_STAT_MULTIPLIER_FACTOR,
)


SPAWN_RADIUS_RANGES = {
    EnemyType.BASIC: (500.0, 1000.0),
    EnemyType.EXPLOSIVE: (800.0, 1000.0),
    EnemyType.TANKER: (200.0, 500.0),
    EnemyType.ASSASSIN: (200.0, 300.0),
    EnemyType.ARCHER: (600.0, 800.0),
}


# Each entry applies to a 10-wave cycle: index 0 -> waves 1, 11, 21, ...
# Values are ((type, percent), ...). Wave n always spawns n * 10 enemies.
WAVE_GROUP_RATIOS = (
    ((EnemyType.BASIC, 100),),
    ((EnemyType.BASIC, 90), (EnemyType.ARCHER, 10)),
    (
        (EnemyType.BASIC, 80),
        (EnemyType.TANKER, 10),
        (EnemyType.ARCHER, 10),
    ),
    (
        (EnemyType.BASIC, 70),
        (EnemyType.EXPLOSIVE, 10),
        (EnemyType.TANKER, 10),
        (EnemyType.ARCHER, 10),
    ),
    (
        (EnemyType.BASIC, 60),
        (EnemyType.EXPLOSIVE, 10),
        (EnemyType.TANKER, 10),
        (EnemyType.ASSASSIN, 10),
        (EnemyType.ARCHER, 10),
    ),
    (
        (EnemyType.BASIC, 50),
        (EnemyType.EXPLOSIVE, 10),
        (EnemyType.TANKER, 20),
        (EnemyType.ASSASSIN, 10),
        (EnemyType.ARCHER, 10),
    ),
    (
        (EnemyType.BASIC, 40),
        (EnemyType.EXPLOSIVE, 30),
        (EnemyType.TANKER, 20),
        (EnemyType.ARCHER, 10),
    ),
    (
        (EnemyType.BASIC, 30),
        (EnemyType.EXPLOSIVE, 10),
        (EnemyType.TANKER, 30),
        (EnemyType.ASSASSIN, 20),
        (EnemyType.ARCHER, 10),
    ),
    (
        (EnemyType.BASIC, 20),
        (EnemyType.EXPLOSIVE, 10),
        (EnemyType.TANKER, 20),
        (EnemyType.ARCHER, 50),
    ),
    (
        (EnemyType.BASIC, 20),
        (EnemyType.EXPLOSIVE, 20),
        (EnemyType.TANKER, 20),
        (EnemyType.ASSASSIN, 20),
        (EnemyType.ARCHER, 20),
    ),
)


def validate_wave(wave):
    if not isinstance(wave, int) or not 1 <= wave <= TOTAL_WAVES:
        raise ValueError(
            "wave must be an integer in the range 1..{}".format(TOTAL_WAVES)
        )


def wave_group(wave):
    validate_wave(wave)
    return WAVE_GROUP_RATIOS[(wave - 1) % len(WAVE_GROUP_RATIOS)]


def wave_enemy_count(wave):
    validate_wave(wave)
    return wave * WAVE_ENEMIES_PER_WAVE


def wave_composition(wave):
    total = wave_enemy_count(wave)
    composition = OrderedDict()
    for enemy_type, percent in wave_group(wave):
        composition[enemy_type] = total * percent // 100
    if sum(composition.values()) != total:
        raise ValueError(
            "wave {} composition does not sum to {}".format(wave, total)
        )
    return composition


def build_wave_spawn_order(wave, random_source=None):
    order = []
    for enemy_type, count in wave_composition(wave).items():
        order.extend([enemy_type] * count)
    if random_source is not None:
        random_source.shuffle(order)
    return order


def wave_stat_multiplier(wave):
    validate_wave(wave)
    return WAVE_STAT_MULTIPLIER_FACTOR ** (wave // WAVE_STAT_MULTIPLIER_EVERY)


def spawn_radius_range(enemy_type):
    try:
        return SPAWN_RADIUS_RANGES[enemy_type]
    except KeyError as error:
        raise ValueError("unsupported enemy type: {!r}".format(enemy_type)) from error


def random_spawn_position(
    enemy_type,
    player_x,
    player_y,
    world_width,
    world_height,
    random_source,
):
    min_radius, max_radius = spawn_radius_range(enemy_type)
    angle = random_source.uniform(0.0, 2.0 * math.pi)
    radius = random_source.uniform(min_radius, max_radius)
    x = player_x + math.cos(angle) * radius
    y = player_y + math.sin(angle) * radius
    x = min(max(x, 0.0), world_width)
    y = min(max(y, 0.0), world_height)
    return x, y


class WaveDirector:
    """Schedules enemy spawns for the current wave at a fixed rate."""

    def __init__(
        self,
        total_waves=TOTAL_WAVES,
        spawn_rate=WAVE_SPAWN_RATE_PER_SECOND,
        random_source=None,
    ):
        if total_waves < 1:
            raise ValueError("total_waves must be positive")
        if spawn_rate <= 0:
            raise ValueError("spawn_rate must be positive")
        self.total_waves = int(total_waves)
        self.spawn_rate = float(spawn_rate)
        self.random_source = random_source or random.Random()
        self.current_wave = 1
        self._spawn_accumulator = 0.0
        self._queue = deque(self._build_order(self.current_wave))
        self.spawned_count = 0

    def _build_order(self, wave):
        return build_wave_spawn_order(wave, self.random_source)

    @property
    def all_spawned(self):
        return not self._queue

    @property
    def total_to_spawn(self):
        return len(self._queue) + self.spawned_count

    @property
    def is_last_wave(self):
        return self.current_wave >= self.total_waves

    def pending_spawns(self, delta_time):
        if delta_time < 0:
            raise ValueError("delta_time must be non-negative")
        self._spawn_accumulator += self.spawn_rate * delta_time
        count = int(self._spawn_accumulator)
        if count <= 0:
            return []
        self._spawn_accumulator -= count
        spawned = []
        for _ in range(min(count, len(self._queue))):
            spawned.append(self._queue.popleft())
            self.spawned_count += 1
        return spawned

    def advance(self):
        if self.is_last_wave:
            return False
        self.current_wave += 1
        self._queue = deque(self._build_order(self.current_wave))
        self.spawned_count = 0
        self._spawn_accumulator = 0.0
        return True

