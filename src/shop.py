from dataclasses import dataclass
from enum import Enum

from weapon import DEFAULT_GUN_ID, MACHINE_GUN_GUN_ID, RIFLE_GUN_ID


GUN_PRICES = {
    DEFAULT_GUN_ID: 0,
    RIFLE_GUN_ID: 100000,
    MACHINE_GUN_GUN_ID: 1000000,
}

GUN_SHOP_ORDER = (
    DEFAULT_GUN_ID,
    RIFLE_GUN_ID,
    MACHINE_GUN_GUN_ID,
)

UPGRADE_COSTS = {
    DEFAULT_GUN_ID: (10, 100, 200, 400, 800, 1000, 2000, 4000, 8000, 10000),
    RIFLE_GUN_ID: (100, 500, 1000, 2000, 4000, 8000, 10000, 15000, 20000, 40000),
    MACHINE_GUN_GUN_ID: (
        1000,
        5000,
        10000,
        20000,
        30000,
        50000,
        60000,
        70000,
        80000,
        100000,
    ),
}

MAX_UPGRADE_LEVEL = 10

UPGRADE_PROBABILITIES = (
    (100, 0, 0, 0),
    (90, 9, 1, 0),
    (80, 18, 2, 0),
    (70, 27, 3, 0),
    (60, 36, 4, 0),
    (50, 44, 5, 1),
    (40, 52, 6, 2),
    (30, 60, 7, 3),
    (20, 68, 8, 4),
    (10, 76, 9, 5),
)


def gun_price(gun_id):
    if gun_id not in GUN_PRICES:
        raise KeyError("unknown gun: {}".format(gun_id))
    return GUN_PRICES[gun_id]


def upgrade_cost(gun_id, level):
    if gun_id not in UPGRADE_COSTS:
        raise KeyError("unknown gun: {}".format(gun_id))
    if level < 0 or level >= MAX_UPGRADE_LEVEL:
        raise IndexError("invalid upgrade level: {}".format(level))
    return UPGRADE_COSTS[gun_id][level]


@dataclass(frozen=True)
class UpgradeChances:
    success: int
    failure: int
    downgrade: int
    destroy: int


def upgrade_chances(level):
    if level < 0 or level >= MAX_UPGRADE_LEVEL:
        raise IndexError("invalid upgrade level: {}".format(level))
    success, failure, downgrade, destroy = UPGRADE_PROBABILITIES[level]
    return UpgradeChances(success, failure, downgrade, destroy)


class PurchaseResult(Enum):
    PURCHASED = "purchased"
    ALREADY_OWNED = "already_owned"
    INSUFFICIENT_COINS = "insufficient_coins"


@dataclass(frozen=True)
class PurchaseOutcome:
    result: PurchaseResult
    gun_id: str
    cost: int
    coins_after: int


def purchase_gun(state, gun_id):
    price = gun_price(gun_id)
    if state.owns_gun(gun_id):
        return PurchaseOutcome(
            PurchaseResult.ALREADY_OWNED,
            gun_id,
            0,
            state.coins,
        )
    if state.coins < price:
        return PurchaseOutcome(
            PurchaseResult.INSUFFICIENT_COINS,
            gun_id,
            price,
            state.coins,
        )
    state.coins -= price
    state.owned_guns.append(gun_id)
    return PurchaseOutcome(
        PurchaseResult.PURCHASED,
        gun_id,
        price,
        state.coins,
    )
