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


def gun_price(gun_id):
    if gun_id not in GUN_PRICES:
        raise KeyError("unknown gun: {}".format(gun_id))
    return GUN_PRICES[gun_id]


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
