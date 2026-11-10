"""Coin rewards and magazine pickups dropped by defeated enemies."""

import math
import random

from game_config import (
    COIN_REWARD_MAX,
    COIN_REWARD_MIN,
    MAGAZINE_DROP_TIERS,
    PICKUP_COLLECT_MARGIN,
    PICKUP_RADIUS,
)


def roll_coin_reward(random_source=None):
    rng = random_source if random_source is not None else random
    return rng.randint(COIN_REWARD_MIN, COIN_REWARD_MAX)


def magazine_drop_chance(total_ammo):
    if total_ammo < 0:
        raise ValueError("total_ammo must be non-negative")
    for upper_bound, chance in MAGAZINE_DROP_TIERS:
        if total_ammo < upper_bound:
            return chance
    return 0.0


def roll_magazine_drop(total_ammo, random_source=None):
    rng = random_source if random_source is not None else random
    return rng.random() < magazine_drop_chance(total_ammo)


class MagazinePickup:
    """Ammunition lying on the map, collected by walking close to it."""

    def __init__(self, x, y, amount, radius=PICKUP_RADIUS):
        if amount <= 0:
            raise ValueError("pickup amount must be positive")
        if radius < 0:
            raise ValueError("pickup radius must be non-negative")
        self.x = float(x)
        self.y = float(y)
        self.amount = int(amount)
        self.radius = float(radius)

    def can_collect(self, player):
        distance = math.hypot(player.x - self.x, player.y - self.y)
        return (
            distance
            <= player.radius + self.radius + PICKUP_COLLECT_MARGIN
        )
