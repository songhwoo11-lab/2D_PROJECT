"""Coin rewards and pickups dropped by defeated enemies."""

import math
import random

from game_config import (
    COIN_REWARD_MAX,
    COIN_REWARD_MIN,
    HEALTH_PICKUP_HEAL,
    MAGAZINE_DROP_TIERS,
    PICKUP_COLLECT_MARGIN,
    PICKUP_DRAW_SIZE,
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


def health_drop_chance(hp, max_hp):
    if max_hp <= 0:
        raise ValueError("max_hp must be positive")
    missing_hp = min(max(max_hp - hp, 0), max_hp)
    return missing_hp / max_hp


def roll_health_drop(hp, max_hp, random_source=None):
    rng = random_source if random_source is not None else random
    return rng.random() < health_drop_chance(hp, max_hp)


class Pickup:
    """An item lying on the map, collected by walking close to it."""

    def __init__(self, x, y, radius=PICKUP_RADIUS, image=None):
        if radius < 0:
            raise ValueError("pickup radius must be non-negative")
        self.x = float(x)
        self.y = float(y)
        self.radius = float(radius)
        self.image = image

    def can_collect(self, player):
        distance = math.hypot(player.x - self.x, player.y - self.y)
        return (
            distance
            <= player.radius + self.radius + PICKUP_COLLECT_MARGIN
        )

    def draw(self, screen_x, screen_y, size=PICKUP_DRAW_SIZE):
        if self.image is None:
            return False
        self.image.draw(screen_x, screen_y, size, size)
        return True


class MagazinePickup(Pickup):
    def __init__(self, x, y, amount, radius=PICKUP_RADIUS, image=None):
        if amount <= 0:
            raise ValueError("pickup amount must be positive")
        super().__init__(x, y, radius, image)
        self.amount = int(amount)


class HealthPickup(Pickup):
    def __init__(
        self,
        x,
        y,
        amount=HEALTH_PICKUP_HEAL,
        radius=PICKUP_RADIUS,
        image=None,
    ):
        if amount <= 0:
            raise ValueError("pickup amount must be positive")
        super().__init__(x, y, radius, image)
        self.amount = int(amount)
