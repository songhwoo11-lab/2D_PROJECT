import random
from dataclasses import dataclass
from enum import Enum

from weapon import (
    DEFAULT_GUN_ID,
    MACHINE_GUN_GUN_ID,
    RIFLE_GUN_ID,
    weapon_display_name,
)


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


class UpgradeResult(Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    DOWNGRADE = "downgrade"
    DESTROY = "destroy"
    NOT_OWNED = "not_owned"
    MAX_LEVEL = "max_level"
    INSUFFICIENT_COINS = "insufficient_coins"


@dataclass(frozen=True)
class PurchaseOutcome:
    result: PurchaseResult
    gun_id: str
    cost: int
    coins_after: int


@dataclass(frozen=True)
class UpgradeOutcome:
    result: UpgradeResult
    gun_id: str
    level_before: int
    level_after: int
    cost: int
    refund: int
    coins_after: int
    roll: int


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


def upgrade_gun(state, gun_id, roll=None):
    if not state.owns_gun(gun_id):
        return UpgradeOutcome(
            UpgradeResult.NOT_OWNED,
            gun_id,
            state.upgrade_level(gun_id),
            state.upgrade_level(gun_id),
            0,
            0,
            state.coins,
            0,
        )

    level = state.upgrade_level(gun_id)
    if level >= MAX_UPGRADE_LEVEL:
        return UpgradeOutcome(
            UpgradeResult.MAX_LEVEL,
            gun_id,
            level,
            level,
            0,
            0,
            state.coins,
            0,
        )

    cost = upgrade_cost(gun_id, level)
    if state.coins < cost:
        return UpgradeOutcome(
            UpgradeResult.INSUFFICIENT_COINS,
            gun_id,
            level,
            level,
            cost,
            0,
            state.coins,
            0,
        )

    state.coins -= cost
    if roll is None:
        roll = random.randint(1, 100)
    if not 1 <= roll <= 100:
        raise ValueError("roll must be between 1 and 100")

    chances = upgrade_chances(level)
    if level == 0 or roll <= chances.success:
        new_level = min(level + 1, MAX_UPGRADE_LEVEL)
        result = UpgradeResult.SUCCESS
        refund = 0
    elif roll <= chances.success + chances.failure:
        new_level = level
        result = UpgradeResult.FAILURE
        refund = cost * 50 // 100
    elif roll <= chances.success + chances.failure + chances.downgrade:
        new_level = max(level - 1, 0)
        result = UpgradeResult.DOWNGRADE
        refund = cost * 70 // 100
    else:
        new_level = 0
        result = UpgradeResult.DESTROY
        refund = cost

    state.set_upgrade_level(gun_id, new_level)
    state.coins += refund
    return UpgradeOutcome(
        result,
        gun_id,
        level,
        new_level,
        cost,
        refund,
        state.coins,
        roll,
    )


def purchase_result_message(outcome):
    name = weapon_display_name(outcome.gun_id)
    if outcome.result is PurchaseResult.PURCHASED:
        return "PURCHASED {} (-{})".format(name, outcome.cost)
    if outcome.result is PurchaseResult.ALREADY_OWNED:
        return "{} IS ALREADY OWNED".format(name)
    return "NOT ENOUGH COINS FOR {}".format(name)


def upgrade_result_message(outcome):
    name = weapon_display_name(outcome.gun_id)
    if outcome.result is UpgradeResult.SUCCESS:
        return "UPGRADE SUCCESS: {} LV {} -> {}".format(
            name,
            outcome.level_before,
            outcome.level_after,
        )
    if outcome.result is UpgradeResult.FAILURE:
        return "UPGRADE FAILED: {}% REFUNDED ({} COINS)".format(
            outcome.refund * 100 // outcome.cost,
            outcome.refund,
        )
    if outcome.result is UpgradeResult.DOWNGRADE:
        return "UPGRADE DOWN: {} LV {} -> {} ({} REFUNDED)".format(
            name,
            outcome.level_before,
            outcome.level_after,
            outcome.refund,
        )
    if outcome.result is UpgradeResult.DESTROY:
        return "{} DESTROYED: LV RESET ({} REFUNDED)".format(
            name,
            outcome.refund,
        )
    if outcome.result is UpgradeResult.NOT_OWNED:
        return "BUY {} BEFORE UPGRADING".format(name)
    if outcome.result is UpgradeResult.MAX_LEVEL:
        return "{} IS ALREADY MAX LEVEL".format(name)
    return "NOT ENOUGH COINS TO UPGRADE {}".format(name)
