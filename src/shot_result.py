"""Shot outcome probability and damage rules from the product requirements."""

from enum import Enum
import random

from game_config import HEADSHOT_CHANCE, MISS_CHANCE


class HitResult(Enum):
    HEADSHOT = "headshot"
    MISS = "miss"
    HIT = "hit"


def resolve_hit_roll(value):
    if not 0.0 <= value < 1.0:
        raise ValueError("hit roll must be in the range [0, 1)")
    if value < HEADSHOT_CHANCE:
        return HitResult.HEADSHOT
    if value < HEADSHOT_CHANCE + MISS_CHANCE:
        return HitResult.MISS
    return HitResult.HIT


def roll_hit_result():
    return resolve_hit_roll(random.random())


def damage_for_result(base_damage, result):
    if result is HitResult.HEADSHOT:
        return base_damage * 3
    if result is HitResult.MISS:
        return 0
    return base_damage
