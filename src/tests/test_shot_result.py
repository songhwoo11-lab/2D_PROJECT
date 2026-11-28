import unittest
from unittest.mock import patch

import game_config
from game_config import HEADSHOT_CHANCE
from shot_result import HitResult, damage_for_result, resolve_hit_roll, roll_hit_result


class ShotResultTests(unittest.TestCase):
    def test_miss_result_and_chance_are_removed(self):
        self.assertFalse(hasattr(HitResult, "MISS"))
        self.assertFalse(hasattr(game_config, "MISS_CHANCE"))

    def test_headshot_range_is_unchanged(self):
        self.assertIs(resolve_hit_roll(0.0), HitResult.HEADSHOT)
        self.assertIs(resolve_hit_roll(HEADSHOT_CHANCE - 0.001), HitResult.HEADSHOT)
        self.assertIs(resolve_hit_roll(HEADSHOT_CHANCE), HitResult.HIT)

    def test_removed_miss_range_now_counts_as_hit(self):
        self.assertIs(resolve_hit_roll(0.05), HitResult.HIT)
        self.assertIs(resolve_hit_roll(0.099), HitResult.HIT)

    def test_hit_probability_includes_the_former_miss_band(self):
        rolls = [index / 1000 for index in range(1000)]
        results = [resolve_hit_roll(value) for value in rolls]

        self.assertEqual(results.count(HitResult.HEADSHOT), 10)
        self.assertEqual(results.count(HitResult.HIT), 990)
        self.assertNotIn("miss", [result.value for result in results])

    def test_roll_hit_result_only_returns_headshot_or_hit(self):
        with patch("shot_result.random.random", side_effect=[0.0, 0.05, 0.9]):
            results = [roll_hit_result() for _ in range(3)]

        self.assertEqual(
            results,
            [HitResult.HEADSHOT, HitResult.HIT, HitResult.HIT],
        )

    def test_damage_for_hit_and_headshot(self):
        self.assertEqual(damage_for_result(10, HitResult.HIT), 10)
        self.assertEqual(damage_for_result(10, HitResult.HEADSHOT), 30)

    def test_invalid_roll_still_raises(self):
        with self.assertRaises(ValueError):
            resolve_hit_roll(-0.01)
        with self.assertRaises(ValueError):
            resolve_hit_roll(1.0)
