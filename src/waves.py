"""Wave composition data for the 30-wave survival mode."""

from collections import OrderedDict

from enemy import EnemyType
from game_config import TOTAL_WAVES


# Each entry applies to a 10-wave cycle: index 0 -> waves 1, 11, 21, ...
# Values are (total enemy count, ((type, percent), ...)).
WAVE_GROUPS = (
    (
        100,
        ((EnemyType.BASIC, 100),),
    ),
    (
        120,
        ((EnemyType.BASIC, 90), (EnemyType.ARCHER, 10)),
    ),
    (
        140,
        (
            (EnemyType.BASIC, 80),
            (EnemyType.TANKER, 10),
            (EnemyType.ARCHER, 10),
        ),
    ),
    (
        160,
        (
            (EnemyType.BASIC, 70),
            (EnemyType.EXPLOSIVE, 10),
            (EnemyType.TANKER, 10),
            (EnemyType.ARCHER, 10),
        ),
    ),
    (
        180,
        (
            (EnemyType.BASIC, 60),
            (EnemyType.EXPLOSIVE, 10),
            (EnemyType.TANKER, 10),
            (EnemyType.ASSASSIN, 10),
            (EnemyType.ARCHER, 10),
        ),
    ),
    (
        200,
        (
            (EnemyType.BASIC, 50),
            (EnemyType.EXPLOSIVE, 10),
            (EnemyType.TANKER, 20),
            (EnemyType.ASSASSIN, 10),
            (EnemyType.ARCHER, 10),
        ),
    ),
    (
        230,
        (
            (EnemyType.BASIC, 40),
            (EnemyType.EXPLOSIVE, 30),
            (EnemyType.TANKER, 20),
            (EnemyType.ARCHER, 10),
        ),
    ),
    (
        270,
        (
            (EnemyType.BASIC, 30),
            (EnemyType.EXPLOSIVE, 10),
            (EnemyType.TANKER, 30),
            (EnemyType.ASSASSIN, 20),
            (EnemyType.ARCHER, 10),
        ),
    ),
    (
        300,
        (
            (EnemyType.BASIC, 20),
            (EnemyType.EXPLOSIVE, 10),
            (EnemyType.TANKER, 20),
            (EnemyType.ARCHER, 50),
        ),
    ),
    (
        500,
        (
            (EnemyType.BASIC, 20),
            (EnemyType.EXPLOSIVE, 20),
            (EnemyType.TANKER, 20),
            (EnemyType.ASSASSIN, 20),
            (EnemyType.ARCHER, 20),
        ),
    ),
)


def validate_wave(wave):
    if not isinstance(wave, int) or not 1 <= wave <= TOTAL_WAVES:
        raise ValueError(
            "wave must be an integer in the range 1..{}".format(TOTAL_WAVES)
        )


def wave_group(wave):
    validate_wave(wave)
    return WAVE_GROUPS[(wave - 1) % len(WAVE_GROUPS)]


def wave_enemy_count(wave):
    return wave_group(wave)[0]


def wave_composition(wave):
    total, entries = wave_group(wave)
    composition = OrderedDict()
    for enemy_type, percent in entries:
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
